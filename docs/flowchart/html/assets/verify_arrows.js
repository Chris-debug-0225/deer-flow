// DeerFlow 流程图 — 箭头对齐运行时自检（自驱动，无外部依赖，无需 mermaid 回调）
// 原理：把每条 edge path 的首尾端点(SVG 用户坐标)经 getScreenCTM 转为屏幕坐标，
//       判断是否落在某个 node 的屏幕边界框附近(容差像素)。若端点漂离所有节点，
//       判定为"箭头错位"。脚本自行轮询直到全部图渲染完，结果写入横幅 + 控制台。
(function () {
  var TOL = 16; // 像素容差，覆盖 marker 大小与边距

  // 把 flowchart 边简化为"最多 1 个拐角的 L 形"（或 0 拐角直线）。
  // 原因：mermaid dagre 的 stepAfter 路由会用"出端口→汇流通道→入端口"多段正交折线，
  //       本该 1 个拐角的连接被拆成 5~6 个小拐角，观感杂乱。
  // 做法：
  //   1) 贝塞尔 C/Q → L（取终点）；
  //   2) 解析出折线首尾端点 (P0, Pn)；
  //   3) 同列(dx≈0) 或同行(dy≈0) → 一段直线，0 拐角；
  //   4) 否则 → 1 个拐角的 L 形。拐角方向按图主流方向：
  //        - 垂直流(TB)：先水平后垂直 → 拐角 (Pn.x, P0.y)，箭头垂直向下进目标顶部；
  //        - 水平流(LR)：先垂直后水平 → 拐角 (P0.x, Pn.y)，箭头水平进入目标侧。
  //   主流方向由本图所有边的总位移 |Σdx| vs |Σdy| 判定。
  // 端点坐标不变，箭头位置不变，杜绝斜线段与多余拐角。
  function parsePts(d) {
    var pts = [];
    var re = /([ML])\s*([-\d.,\s]+)/g, mch;
    while ((mch = re.exec(d)) !== null) {
      var nums = mch[2].trim().split(/[\s,]+/);
      for (var i = 0; i + 1 < nums.length; i += 2)
        pts.push([parseFloat(nums[i]), parseFloat(nums[i + 1])]);
    }
    return pts;
  }

  // 取本图所有节点在【屏幕坐标】下的边界框（getBoundingClientRect，最可靠）。
  // 返回 { nodeId: {l,t,r,b} }。path 的 d 是用户坐标，snap 时用 getScreenCTM 在
  // 用户坐标 ↔ 屏幕坐标 间转换，避免 getCTM/getBBox 的坐标系系统性偏差。
  function nodeScreenBounds(svg) {
    var map = {};
    Array.prototype.forEach.call(svg.querySelectorAll('g.node'), function (n) {
      var raw = n.getAttribute('id') || '';
      var nid = raw.replace(/^flowchart-/, '').replace(/-\d+$/, '');
      var r = n.getBoundingClientRect();
      map[nid] = { l: r.left, t: r.top, r: r.right, b: r.bottom };
    });
    return map;
  }

  function simplifyAll() {
    var EPS = 0.6;
    document.querySelectorAll('pre.mermaid svg').forEach(function (svg) {
      var edges = svg.querySelectorAll('path.flowchart-link');
      if (!edges.length) return;
      var ctm = svg.getScreenCTM();
      if (!ctm) return;
      var inv = ctm.inverse();
      function u2s(x, y) { var p = svg.createSVGPoint(); p.x = x; p.y = y; return p.matrixTransform(ctm); }
      function s2u(x, y) { var p = svg.createSVGPoint(); p.x = x; p.y = y; return p.matrixTransform(inv); }
      var nb = nodeScreenBounds(svg); // 节点屏幕边界
      // 算 marker 尖端相对 path 终点的偏移 GAP：marker 三角尖端在 viewBox x=10，
      // refX 是对齐到终点的点。尖端 = 终点 + 末端方向 * GAP。
      // 规范要求尖端落节点边缘，故 snap 终点应停在边缘【外侧 GAP】，让尖端正好顶到边。
      var GAP = 4;
      try {
        var e0 = edges[0];
        var sw = parseFloat(getComputedStyle(e0).strokeWidth) || 1;
        var me = (e0.getAttribute('marker-end') || '').match(/url\(#([^)]+)\)/);
        if (me) {
          var mk = document.querySelector('marker#' + me[1]);
          if (mk) {
            var refX = parseFloat(mk.getAttribute('refX')) || 5;
            var mkW = parseFloat(mk.getAttribute('markerWidth')) || 8;
            var vb = (mk.getAttribute('viewBox') || '0 0 10 10').split(/\s+/);
            var vbW = parseFloat(vb[2]) || 10;
            GAP = (10 - refX) / vbW * mkW * sw; // viewBox 尖端 x=10
          }
        }
      } catch (eg) { /* 取默认 GAP */ }
      // snap 端点（屏幕坐标）到最近节点的真实边缘，退后 GAP 让 marker 尖端正好顶到边。
      // 选边策略：按该端点处 path 段的方向选——源端按首段方向(流出边)，目标端按末段方向
      // (流入边)。dagre 保证首段从源流出、末段指向目标节点内，故 snap 到方向对应的边后，
      // 末端段方向仍指向节点，marker 尖端(终点+方向×GAP)正好落在边缘。
      // dir=[dx,dy]：该端的 path 段方向（用户坐标）。isVert 段为垂直(选顶/底)，否则水平(选左/右)。
      function snapEdgePt(px, py, dir) {
        var sp = u2s(px, py);
        var best = null;
        for (var k in nb) {
          var nd = nb[k];
          var dxo = 0, dyo = 0;
          if (sp.x < nd.l) dxo = nd.l - sp.x; else if (sp.x > nd.r) dxo = sp.x - nd.r;
          if (sp.y < nd.t) dyo = nd.t - sp.y; else if (sp.y > nd.b) dyo = sp.y - nd.b;
          var dd = Math.hypot(dxo, dyo);
          if (!best || dd < best.d) best = { d: dd, nd: nd };
        }
        if (!best) return [px, py];
        var nd = best.nd;
        // 按方向绝对值选轴：|dir.y|>|dir.x|→垂直段(顶/底)，否则水平段(左/右)
        if (Math.abs(dir[1]) > Math.abs(dir[0])) {
          // 垂直段：dir.y>0 向下→snap 底边(端点在下方)，dir.y<0→顶边
          sp.y = (dir[1] > 0) ? (nd.b + GAP) : (nd.t - GAP);
          if (sp.x < nd.l) sp.x = nd.l; else if (sp.x > nd.r) sp.x = nd.r;
        } else {
          // 水平段：dir.x>0 向右→snap 右边，dir.x<0→左边
          sp.x = (dir[0] > 0) ? (nd.r + GAP) : (nd.l - GAP);
          if (sp.y < nd.t) sp.y = nd.t; else if (sp.y > nd.b) sp.y = nd.b;
        }
        var up = s2u(sp.x, sp.y);
        return [up.x, up.y];
      }
      edges.forEach(function (e) {
        var pts = parsePts(e.getAttribute('d') || '');
        if (pts.length < 2) return;
        var p0 = [pts[0][0], pts[0][1]], pn = [pts[pts.length - 1][0], pts[pts.length - 1][1]];
        // 首段方向 = pts[1]-pts[0]；末段方向 = pn - pts[len-2]（dagre 保证指向目标）
        var p1 = pts.length >= 2 ? pts[1] : pn;
        var pnm1 = pts.length >= 2 ? pts[pts.length - 2] : p0;
        var dir0 = [p1[0] - p0[0], p1[1] - p0[1]];        // 首段（源端流出方向）
        var dirN = [pn[0] - pnm1[0], pn[1] - pnm1[1]];    // 末段（目标端流入方向）
        var dx = pn[0] - p0[0], dy = pn[1] - p0[1];
        var isVert = Math.abs(dy) >= Math.abs(dx); // 主走向定 L 折线形式

        // —— 端点 snap 到源/目标节点真实边缘（按首/末段方向定边）——
        // 规范：箭头尖端必须正好落在目标方框边缘轮廓上（不悬空、不穿透）。
        // dagre 为 marker 预留 ~5px，path 终点悬空在边缘外。snap 后退后 GAP，
        // 使 marker 尖端（在终点外 GAP 处、沿末端段方向）正好顶到方框边缘。
        var np0 = snapEdgePt(p0[0], p0[1], dir0); p0[0] = np0[0]; p0[1] = np0[1];
        var npn = snapEdgePt(pn[0], pn[1], dirN); pn[0] = npn[0]; pn[1] = npn[1];

        var nd;
        if (Math.abs(pn[0] - p0[0]) < EPS || Math.abs(pn[1] - p0[1]) < EPS) {
          // 同列或同行：一段直线，0 拐角
          nd = 'M' + p0[0] + ',' + p0[1] + 'L' + pn[0] + ',' + pn[1];
        } else if (targetVert) {
          // 目标垂直进入：先水平后垂直，拐角在 (pn.x, p0.y)，箭头垂直进入目标顶/底
          nd = 'M' + p0[0] + ',' + p0[1] + 'L' + pn[0] + ',' + p0[1] + 'L' + pn[0] + ',' + pn[1];
        } else {
          // 目标水平进入：先垂直后水平，拐角在 (p0.x, pn.y)，箭头水平进入目标左/右
          nd = 'M' + p0[0] + ',' + p0[1] + 'L' + p0[0] + ',' + pn[1] + 'L' + pn[0] + ',' + pn[1];
        }
        e.setAttribute('d', nd);
      });
    });
  }




  function inspect() {
    var svgs = document.querySelectorAll('pre.mermaid svg');
    var pres = document.querySelectorAll('pre.mermaid');
    if (!svgs.length || svgs.length < pres.length) return null; // 尚未全部渲染

    var totalEdges = 0, badEdges = 0;
    var perSvg = [];
    svgs.forEach(function (svg, idx) {
      var ctm = svg.getScreenCTM();
      if (!ctm) return;
      function toScreen(p) {
        var pt = svg.createSVGPoint();
        pt.x = p.x; pt.y = p.y;
        return pt.matrixTransform(ctm);
      }
      var rects = Array.prototype.map.call(svg.querySelectorAll('g.node'), function (n) {
        var r = n.getBoundingClientRect();
        return { l: r.left, t: r.top, r: r.right, b: r.bottom };
      });
      // 边：只取 flowchart 专属的 flowchart-link 边（带 marker-end）。
      // 这样自动跳过 stateDiagram（transition/note 关联线）与 sequenceDiagram（消息箭头），
      // 避免对不同图类型的渲染特性误判。用户关注的是 flowchart 的箭头-方框对齐。
      var edges = svg.querySelectorAll('g.edgePaths path.flowchart-link, path.flowchart-link');
      if (!rects.length || !edges.length) return; // 此图无边或无节点，跳过
      var svgEdges = 0, svgBad = 0;
      edges.forEach(function (ep) {
        var len;
        try { len = ep.getTotalLength(); } catch (e) { return; }
        if (!len || len < 2) return;
        svgEdges++; totalEdges++;
        var s0 = toScreen(ep.getPointAtLength(1));
        var s1 = toScreen(ep.getPointAtLength(len - 1));
        function near(sp) {
          return rects.some(function (rc) {
            return sp.x >= rc.l - TOL && sp.x <= rc.r + TOL &&
                   sp.y >= rc.t - TOL && sp.y <= rc.b + TOL;
          });
        }
        if (!near(s0) || !near(s1)) { svgBad++; badEdges++; }
      });
      if (svgEdges) perSvg.push({ idx: idx + 1, edges: svgEdges, bad: svgBad });
    });

    return { totalEdges: totalEdges, badEdges: badEdges, pass: badEdges === 0, details: perSvg };
  }

  function emit(rep) {
    if (!rep) return false;
    var summary = '[箭头对齐自检] ' + rep.details.length + ' 张图 / ' + rep.totalEdges +
                  ' 条边 / 错位 ' + rep.badEdges + ' 条 → ' + (rep.pass ? 'PASS ✓' : 'FAIL ✗');
    (console[rep.pass ? 'info' : 'warn'])(summary);
    if (rep.details.some(function (p) { return p.bad; }))
      console.table(rep.details.filter(function (p) { return p.bad; }));
    var content = document.querySelector('.content');
    if (content) {
      var banner = document.getElementById('arrow-report');
      if (!banner) {
        banner = document.createElement('div');
        banner.id = 'arrow-report';
        content.insertBefore(banner, content.firstChild);
      }
      banner.className = 'arrow-report ' + (rep.pass ? 'pass' : 'fail');
      banner.textContent = summary;
    }
    window.__arrowReport = rep;
    return true;
  }

  // 手动调用入口（兼容旧调用约定）
  window.__verifyArrows = function () { return emit(inspect()); };

  // 自驱动：轮询直到全部 svg 渲染完并出报告，最多 ~60s
  var tries = 0;
  var timer = setInterval(function () {
    tries++;
    simplifyAll(); // 把每条边简化为最多 1 个拐角的 L 形（无斜线、无多余拐角）
    var rep = inspect();
    if (rep) emit(rep);
    var done = rep && rep.details.length >= document.querySelectorAll('pre.mermaid svg').length;
    if (done || tries > 120) clearInterval(timer);
  }, 500);
})();
