# 认证测试计划

本文档概述 DeerFlow 认证系统的测试策略。

## 测试范围

### 单元测试

#### 令牌生成和验证

```python
class TestTokenGeneration:
    """测试 JWT 令牌的创建和验证。"""

    def test_access_token_creation(self):
        """测试有效的访问令牌创建。"""
        token = create_access_token(user_id="user_123", session_id="session_abc")
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        assert payload["sub"] == "user_123"
        assert payload["sid"] == "session_abc"
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_refresh_token_creation(self):
        """测试有效的刷新令牌创建。"""
        token = create_refresh_token(user_id="user_123", session_id="session_abc")
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        assert payload["type"] == "refresh"
        assert payload["exp"] > payload["iat"] + 86400  # 至少 1 天后过期

    def test_expired_token_rejection(self):
        """测试过期令牌被拒绝。"""
        expired_token = create_token_with_custom_expiry(
            user_id="user_123",
            exp=datetime.utcnow() - timedelta(hours=1)
        )

        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(expired_token, SECRET_KEY, algorithms=["HS256"])

    def test_invalid_signature_rejection(self):
        """测试无效签名被拒绝。"""
        token = create_access_token(user_id="user_123", session_id="session_abc")
        tampered_token = token[:-5] + "xxxxx"

        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(tampered_token, SECRET_KEY, algorithms=["HS256"])
```

#### 会话管理

```python
class TestSessionManagement:
    """测试会话生命周期管理。"""

    async def test_session_creation(self):
        """测试新会话创建。"""
        user = User(id="user_123", email="test@example.com")
        session = await create_session(user, ip="127.0.0.1", user_agent="Test/1.0")

        assert session.user_id == "user_123"
        assert session.id is not None
        assert session.expires_at > datetime.utcnow()

    async def test_session_retrieval(self):
        """测试会话检索。"""
        session = await create_session(User(id="user_123"))
        retrieved = await get_session(session.id)

        assert retrieved is not None
        assert retrieved.id == session.id

    async def test_session_revocation(self):
        """测试会话撤销。"""
        session = await create_session(User(id="user_123"))
        await revoke_session(session.id)

        revoked = await get_session(session.id)
        assert revoked is None or revoked.revoked

    async def test_session_expiration_cleanup(self):
        """测试过期会话清理。"""
        # 创建过期会话
        old_session = await create_session(
            User(id="user_123"),
            expires_at=datetime.utcnow() - timedelta(days=1)
        )

        # 运行清理
        cleaned = await cleanup_expired_sessions()

        assert cleaned > 0
        assert await get_session(old_session.id) is None
```

### 集成测试

#### 登录流程

```python
class TestLoginFlow:
    """测试完整的登录流程。"""

    async def test_github_oauth_flow(self, test_client):
        """测试 GitHub OAuth 登录流程。"""
        # 1. 发起 OAuth 流程
        response = await test_client.get("/auth/github/login")
        assert response.status_code == 302
        assert "github.com" in response.headers["location"]

        # 2. 模拟 OAuth 回调
        mock_code = "test_oauth_code"
        mock_state = response.cookies.get("oauth_state")

        with mock_github_api():
            callback_response = await test_client.get(
                f"/auth/github/callback?code={mock_code}&state={mock_state}"
            )

        assert callback_response.status_code == 302
        assert callback_response.cookies.get("access_token")
        assert callback_response.cookies.get("refresh_token")

    async def test_login_session_fixation_protection(self, test_client):
        """测试会话固定防护。"""
        # 创建初始会话
        initial_response = await test_client.get("/some-endpoint")
        old_session = initial_response.cookies.get("session_id")

        # 登录
        with mock_github_api():
            login_response = await test_client.get(
                "/auth/github/callback?code=test&state=valid"
            )

        new_session = login_response.cookies.get("session_id")
        assert new_session != old_session

    async def test_token_refresh_flow(self, test_client):
        """测试令牌刷新流程。"""
        # 使用过期访问令牌但有效刷新令牌
        test_client.cookies.set("access_token", expired_token)
        test_client.cookies.set("refresh_token", valid_refresh_token)

        response = await test_client.post("/auth/refresh")
        assert response.status_code == 200
        assert response.json()["access_token"]

        # 验证设置了新的 cookie
        assert response.cookies.get("access_token")
```

#### CSRF 防护

```python
class TestCSRFProtection:
    """测试 CSRF 防护机制。"""

    async def test_csrf_token_generation(self, test_client):
        """测试 CSRF 令牌创建。"""
        response = await test_client.get("/auth/csrf-token")
        csrf_token = response.json()["csrf_token"]

        assert csrf_token is not None
        assert len(csrf_token) > 16  # 合理长度

    async def test_post_without_csrf_fails(self, test_client):
        """测试无 CSRF 令牌的 POST 请求失败。"""
        # 登录获取认证
        await login_test_user(test_client)

        # 尝试无 CSRF 令牌创建线程
        response = await test_client.post("/api/threads", json={"title": "Test"})

        assert response.status_code == 403
        assert "CSRF" in response.json()["detail"]

    async def test_post_with_csrf_succeeds(self, test_client):
        """测试有 CSRF 令牌的 POST 请求成功。"""
        # 登录并获取 CSRF 令牌
        await login_test_user(test_client)
        csrf_response = await test_client.get("/auth/csrf-token")
        csrf_token = csrf_response.json()["csrf_token"]

        # 带 CSRF 令牌的请求
        response = await test_client.post(
            "/api/threads",
            json={"title": "Test"},
            headers={"X-CSRF-Token": csrf_token}
        )

        assert response.status_code == 201

    async def test_csrf_token_mismatch_fails(self, test_client):
        """测试 CSRF 令牌不匹配失败。"""
        await login_test_user(test_client)

        # 发送错误的 CSRF 令牌
        response = await test_client.post(
            "/api/threads",
            json={"title": "Test"},
            headers={"X-CSRF-Token": "wrong-token"}
        )

        assert response.status_code == 403
```

### 用户隔离测试

```python
class TestUserIsolation:
    """测试用户数据隔离。"""

    async def test_user_cannot_access_other_threads(self, test_client):
        """测试用户无法访问其他用户的线程。"""
        # 以用户 A 登录并创建线程
        await login_user_a(test_client)
        thread = await create_thread(test_client, "User A Thread")
        thread_id = thread["id"]

        # 以用户 B 登录
        await login_user_b(test_client)

        # 尝试访问用户 A 的线程
        response = await test_client.get(f"/api/threads/{thread_id}")
        assert response.status_code == 404  # 或 403

    async def test_user_cannot_modify_other_threads(self, test_client):
        """测试用户无法修改其他用户的线程。"""
        await login_user_a(test_client)
        thread = await create_thread(test_client, "User A Thread")

        await login_user_b(test_client)
        response = await test_client.delete(f"/api/threads/{thread['id']}")
        assert response.status_code in (403, 404)

    async def test_thread_list_shows_only_own_threads(self, test_client):
        """测试线程列表仅显示自己的线程。"""
        # 用户 A 创建线程
        await login_user_a(test_client)
        await create_thread(test_client, "User A Thread 1")
        await create_thread(test_client, "User A Thread 2")

        # 用户 B 创建线程
        await login_user_b(test_client)
        await create_thread(test_client, "User B Thread")

        # 用户 B 应该只看到 1 个线程
        response = await test_client.get("/api/threads")
        threads = response.json()

        assert len(threads) == 1
        assert threads[0]["title"] == "User B Thread"
```

## 端到端测试

```python
class TestAuthenticationE2E:
    """认证系统的端到端测试。"""

    async def test_full_user_lifecycle(self, test_client):
        """测试完整用户生命周期。"""
        # 1. OAuth 登录
        auth_response = await perform_oauth_login(test_client, provider="github")
        assert auth_response.status_code == 302

        # 2. 访问受保护资源
        threads_response = await test_client.get("/api/threads")
        assert threads_response.status_code == 200

        # 3. 创建线程
        create_response = await test_client.post(
            "/api/threads",
            json={"title": "Test Thread"},
            headers={"X-CSRF-Token": get_csrf_token(test_client)}
        )
        assert create_response.status_code == 201
        thread_id = create_response.json()["id"]

        # 4. 访问线程
        thread_response = await test_client.get(f"/api/threads/{thread_id}")
        assert thread_response.status_code == 200

        # 5. 发送消息
        message_response = await test_client.post(
            f"/api/threads/{thread_id}/runs",
            json={"input": {"messages": [{"role": "user", "content": "Hello"}]}},
            headers={"X-CSRF-Token": get_csrf_token(test_client)}
        )
        assert message_response.status_code == 200

        # 6. 登出
        logout_response = await test_client.post("/auth/logout")
        assert logout_response.status_code == 200

        # 7. 验证会话已撤销
        after_logout = await test_client.get("/api/threads")
        assert after_logout.status_code == 401
```

## 性能测试

```python
class TestAuthPerformance:
    """认证性能测试。"""

    async def test_token_validation_performance(self, benchmark):
        """基准测试令牌验证速度。"""
        token = create_access_token("user_123", "session_abc")

        def validate_token():
            jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        result = benchmark(validate_token)
        assert result.stats.mean < 0.001  # 平均 < 1ms

    async def test_session_creation_throughput(self, test_client):
        """测试会话创建吞吐量。"""
        import asyncio

        async def create_session():
            return await create_session_api(test_client)

        # 并发创建 100 个会话
        tasks = [create_session() for _ in range(100)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if not isinstance(r, Exception))
        assert success_count == 100
```

## 安全测试

```python
class TestAuthSecurity:
    """认证安全测试。"""

    async def test_sql_injection_in_login(self, test_client):
        """测试登录中的 SQL 注入防护。"""
        malicious_email = "user' OR '1'='1'; --@example.com"
        response = await test_client.post(
            "/auth/login",
            json={"email": malicious_email, "password": "password"}
        )
        assert response.status_code in (400, 401, 422)

    async def test_rate_limiting_on_login(self, test_client):
        """测试登录端点的速率限制。"""
        # 快速发送多个登录请求
        for _ in range(10):
            await test_client.post("/auth/login", json={
                "email": "test@example.com",
                "password": "wrong"
            })

        # 第 11 个请求应该被速率限制
        response = await test_client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "wrong"
        })
        assert response.status_code == 429  # Too Many Requests
```

## 测试数据

### 测试用户

```python
TEST_USERS = [
    {
        "id": "user_test_a",
        "email": "user_a@test.com",
        "name": "Test User A",
        "auth_provider": "github",
        "external_id": "github_12345"
    },
    {
        "id": "user_test_b",
        "email": "user_b@test.com",
        "name": "Test User B",
        "auth_provider": "google",
        "external_id": "google_67890"
    }
]
```

### 模拟 OAuth 响应

```python
MOCK_GITHUB_USER = {
    "id": "github_12345",
    "login": "testuser",
    "email": "user_a@test.com",
    "name": "Test User A"
}
```

## CI/CD 集成

```yaml
# .github/workflows/auth-tests.yml
name: Authentication Tests

on: [push, pull_request]

jobs:
  auth-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      - name: Run auth tests
        run: pytest tests/auth/ -v --cov=deerflow.auth
      - name: Generate coverage report
        run: pytest tests/auth/ --cov-report=xml
```

## 运行测试

```bash
# 运行所有认证测试
pytest tests/auth/ -v

# 运行特定测试文件
pytest tests/auth/test_token.py -v

# 运行特定测试
pytest tests/auth/test_csrf.py::TestCSRFProtection::test_post_without_csrf_fails -v

# 带覆盖率
pytest tests/auth/ --cov=deerflow.auth --cov-report=html
```
