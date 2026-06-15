# DeerFlow Memory 系统流程图

本文档包含 Memory 记忆系统的完整 Mermaid 流程图，展示记忆的提取、存储、检索和更新机制。

## 1. Memory 系统架构图

展示 Memory 系统的整体架构和组件关系。

```mermaid
graph TB
    subgraph "输入层"
        Conversation[对话完成] --> MessageFilter[消息过滤器]
        MessageFilter --> UserMsg[用户消息]
        MessageFilter --> AIResp[AI 响应]
    end
    
    subgraph "记忆队列"
        UserMsg --> MemoryQueue[记忆队列]
        AIResp --> MemoryQueue
        
        MemoryQueue --> QueueProcessor[队列处理器]
        QueueProcessor --> BatchExtract[批量提取]
    end
    
    subgraph "记忆提取"
        BatchExtract --> LLMExtract[LLM 提取器]
        LLMExtract --> ExtractSummary[生成摘要]
        ExtractSummary --> ExtractKeyInfo[提取关键信息]
        ExtractKeyInfo --> ExtractEntities[提取实体]
        ExtractKeyInfo --> ExtractActions[提取行动项]
    end
    
    subgraph "记忆处理"
        ExtractSummary --> MemoryObj[创建记忆对象]
        ExtractKeyInfo --> MemoryObj
        ExtractEntities --> MemoryObj
        ExtractActions --> MemoryObj
        
        MemoryObj --> DedupCheck[去重检查]
        DedupCheck --> Similarity[相似度计算]
        Similarity --> MergeDecision{需要合并？}
    end
    
    subgraph "记忆存储"
        MergeDecision -->|是 | MergeMem[合并记忆]
        MergeDecision -->|否 | DirectStore[直接存储]
        
        MergeMem --> StoreMem[存储到数据库]
        DirectStore --> StoreMem
        
        StoreMem --> UpdateIndex[更新索引]
        UpdateIndex --> CreateEmbedding[创建嵌入向量]
        CreateEmbedding --> VectorStore[向量存储]
    end
    
    subgraph "记忆检索"
        NewQuery[新查询] --> RetrieveQuery[检索查询]
        RetrieveQuery --> VectorSearch[向量搜索]
        VectorSearch --> TopK[Top-K 结果]
        TopK --> RankResult[排序结果]
        RankResult --> SelectMem[选择相关记忆]
    end
    
    subgraph "上下文注入"
        SelectMem --> InjectCtx[注入上下文]
        InjectCtx --> BuildPrompt[构建提示词]
        BuildPrompt --> LLMCall[LLM 调用]
    end
    
    subgraph "记忆更新"
        StoreMem --> PeriodicUpdate[定期更新]
        PeriodicUpdate --> MergeSimilar[合并相似记忆]
        MergeSimilar --> PruneOld[清理过期记忆]
        PruneOld --> StoreMem
    end
    
    style Conversation fill:#e1f5ff
    style LLMCall fill:#fff4e1
    style StoreMem fill:#e1ffe1
    style VectorStore fill:#f0e1ff
```

## 2. 记忆提取流程时序图

展示记忆从对话到存储的完整时序。

```mermaid
sequenceDiagram
    participant Thread as 线程
    participant Queue as 记忆队列
    participant Extractor as 提取器
    participant LLM as LLM API
    participant Dedup as 去重模块
    participant Storage as 存储
    
    Thread->>Queue: 添加消息到队列
    
    loop 队列处理
        Queue->>Extractor: 获取批次
        
        alt 有足够消息
            Extractor->>LLM: 请求记忆提取
            LLM-->>Extractor: 返回提取结果
            
            Extractor->>Extractor: 解析提取结果
            Extractor->>Dedup: 检查重复
            
            alt 新记忆
                Dedup-->>Extractor: 唯一
                Extractor->>Storage: 保存记忆
                Storage-->>Extractor: 保存成功
            else 相似记忆
                Dedup-->>Extractor: 相似 ID
                Extractor->>Storage: 更新记忆
                Storage-->>Extractor: 更新成功
            end
            
            Extractor->>Queue: 标记处理完成
        else 消息不足
            Queue->>Queue: 等待更多消息
        end
    end
    
    Thread->>Thread: 继续对话
```

## 3. 记忆检索与注入图

展示记忆检索和注入到 LLM 上下文的流程。

```mermaid
graph TB
    subgraph "查询准备"
        Start[新线程开始] --> GetContext[获取上下文]
        GetContext --> GetThreadInfo[获取线程信息]
        GetThreadInfo --> GetConfig[获取记忆配置]
        GetConfig --> BuildQuery[构建检索查询]
    end
    
    subgraph "向量检索"
        BuildQuery --> CreateEmbedding[创建查询嵌入]
        CreateEmbedding --> VectorSearch[向量相似度搜索]
        VectorSearch --> SimilarityScore[计算相似度]
        SimilarityScore --> FilterMem[过滤低分记忆]
    end
    
    subgraph "结果排序"
        FilterMem --> RankByRecency[按时间排序]
        RankByRecency --> RankByRelevance[按相关性排序]
        RankByRelevance --> RankByImportance[按重要性排序]
        RankByImportance --> FinalRank[最终排序]
    end
    
    subgraph "记忆选择"
        FinalRank --> SelectTopK[选择 Top-K]
        SelectTopK --> CheckLimit{超过限制？}
        CheckLimit -->|是 | TrimMem[裁剪记忆]
        CheckLimit -->|否 | UseMem[使用记忆]
        
        TrimMem --> UseMem
    end
    
    subgraph "上下文构建"
        UseMem --> FormatMem[格式化记忆]
        FormatMem --> AddMetadata[添加元数据]
        AddMetadata --> BuildPromptSection[构建提示部分]
        BuildPromptSection --> InjectCtx[注入上下文]
    end
    
    subgraph "LLM 调用"
        InjectCtx --> CombinePrompt[组合提示词]
        CombinePrompt --> AddSystem[添加系统提示]
        AddSystem --> AddHistory[添加对话历史]
        AddHistory --> LLMCall[调用 LLM]
        LLMCall --> GenerateResp[生成响应]
    end
    
    style Start fill:#e1f5ff
    style GenerateResp fill:#e1ffe1
    style VectorSearch fill:#fff4e1
    style FinalRank fill:#f0e1ff
    style LLMCall fill:#fff4e1
```

## 4. 记忆去重与合并图

展示记忆去重和相似记忆合并的逻辑。

```mermaid
graph TB
    subgraph "新记忆输入"
        Start[新记忆对象] --> Normalize[标准化处理]
        Normalize --> ExtractFeatures[提取特征]
        ExtractFeatures --> GetContent[内容特征]
        ExtractFeatures --> GetTime[时间特征]
        ExtractFeatures --> GetEntities[实体特征]
    end
    
    subgraph "相似度计算"
        GetContent --> ContentSim[内容相似度]
        GetTime --> TimeSim[时间相似度]
        GetEntities --> EntitySim[实体相似度]
        
        ContentSim --> WeightSum[加权求和]
        TimeSim --> WeightSum
        EntitySim --> WeightSum
        
        WeightSum --> FinalScore[最终相似度]
    end
    
    subgraph "去重判断"
        FinalScore --> CheckThreshold{超过阈值？}
        CheckThreshold -->|是 | IsDuplicate[判定为重复]
        CheckThreshold -->|否 | IsUnique[判定为唯一]
        
        IsDuplicate --> GetOriginal[获取原始记忆]
        GetOriginal --> MergeStrategy[选择合并策略]
    end
    
    subgraph "合并策略"
        MergeStrategy --> TimeBased[基于时间]
        MergeStrategy --> ContentBased[基于内容]
        MergeStrategy --> Hybrid[混合策略]
        
        TimeBased --> KeepRecent[保留最近的]
        ContentBased --> MergeContent[合并内容]
        Hybrid --> SmartMerge[智能合并]
    end
    
    subgraph "合并执行"
        KeepRecent --> UpdateOriginal[更新原始记忆]
        MergeContent --> UpdateOriginal
        SmartMerge --> UpdateOriginal
        
        UpdateOriginal --> RecalculateEmbedding[重新计算嵌入]
        RecalculateEmbedding --> UpdateStorage[更新存储]
        UpdateStorage --> Done[完成]
    end
    
    subgraph "唯一记忆"
        IsUnique --> CreateNew[创建新记忆]
        CreateNew --> EmbedNew[创建嵌入向量]
        EmbedNew --> StoreNew[存储到数据库]
        StoreNew --> UpdateIndex[更新索引]
        UpdateIndex --> Done
    end
    
    style Start fill:#e1f5ff
    style Done fill:#e1ffe1
    style WeightSum fill:#fff4e1
    style SmartMerge fill:#f0e1ff
    style UpdateStorage fill:#e1ffe1
```

## 5. 记忆更新与清理图

展示记忆的定期更新和过期清理机制。

```mermaid
graph TB
    subgraph "定期任务"
        Start[定时触发] --> CheckUpdate{更新检查？}
        CheckUpdate -->|是 | FindUpdateMem
        CheckUpdate -->|否 | CheckPrune
    end
    
    subgraph "记忆更新"
        FindUpdateMem[查找可更新记忆] --> AnalyzeMem[分析记忆]
        AnalyzeMem --> CheckStaleness{过时？}
        CheckStaleness -->|是 | MarkUpdate
        CheckStaleness -->|否 | CheckPrune
        
        MarkUpdate[标记为待更新] --> FindRelated[查找相关对话]
        FindRelated --> ReExtract[重新提取]
        ReExtract --> UpdateMem[更新记忆]
        UpdateMem --> RecalculateEmbedding[重新计算嵌入]
        RecalculateEmbedding --> StoreUpdate[更新存储]
    end
    
    subgraph "记忆清理"
        CheckPrune{清理检查？} -->|是 | FindPruneMem
        CheckPrune -->|否 | Done[完成]
        
        FindPruneMem[查找可清理记忆] --> CheckAge{年龄检查}
        CheckAge -->|过期 | MarkPrune
        CheckAge -->|未过期 | Done
        
        MarkPrune[标记为待删除] --> CheckRef{有引用？}
        CheckRef -->|有 | KeepMem
        CheckRef -->|无 | DeleteMem[删除记忆]
    end
    
    subgraph "删除执行"
        DeleteMem --> RemoveDB[从数据库删除]
        RemoveDB --> RemoveVector[从向量库删除]
        RemoveVector --> UpdateIndex[更新索引]
        UpdateIndex --> Done
    end
    
    subgraph "合并执行"
        KeepMem[保留记忆] --> Done
        StoreUpdate --> Done
    end
    
    style Start fill:#e1f5ff
    style Done fill:#e1ffe1
    style ReExtract fill:#fff4e1
    style MarkPrune fill:#ffe1e1
    style StoreUpdate fill:#e1ffe1
```

## 6. 记忆数据结构图

展示记忆对象的数据结构和字段定义。

```mermaid
classDiagram
    class Memory {
        +str id
        +str thread_id
        +str content
        +str summary
        +list entities
        +list actions
        +float importance
        +datetime created_at
        +datetime updated_at
        +dict metadata
        +vector embedding
        +retrieve()
        +update()
        +delete()
    }
    
    class MemoryQueueItem {
        +str message_id
        +str thread_id
        +str role
        +str content
        +datetime added_at
        +process()
    }
    
    class MemoryRetrievalResult {
        +list memories
        +list scores
        +int total_count
        +dict metadata
        +format_for_prompt()
    }
    
    class MemoryConfig {
        +int max_memories
        +float similarity_threshold
        +int retrieval_top_k
        +bool enabled
        +dict extraction_config
        +validate()
        +update()
    }
    
    Memory --> MemoryQueueItem : 从队列创建
    Memory --> MemoryRetrievalResult : 检索返回
    MemoryConfig ..> Memory : 配置
    
    note for Memory "核心记忆对象<br/>包含所有记忆数据"
    note for MemoryQueueItem "队列中的临时项<br/>等待提取"
    note for MemoryRetrievalResult "检索结果包装<br/>用于上下文注入"
    note for MemoryConfig "记忆系统配置<br/>控制行为"
```

## 7. 记忆提取 LLM 提示图

展示用于记忆提取的 LLM 提示结构。

```mermaid
graph TB
    subgraph "系统提示"
        Start[系统提示] --> DefineRole[定义角色]
        DefineRole --> ExplainTask[解释任务]
        ExplainTask --> OutputFormat[定义输出格式]
    end
    
    subgraph "用户消息"
        OutputFormat --> AddContext[添加上下文]
        AddContext --> AddConversation[添加对话片段]
        AddConversation --> AddExamples[添加示例]
    end
    
    subgraph "对话分析"
        AddExamples --> AnalyzeContent[分析内容]
        AnalyzeContent --> IdentifyKey[识别关键点]
        IdentifyKey --> ExtractInfo[提取信息]
    end
    
    subgraph "提取目标"
        ExtractInfo --> Summary[对话摘要]
        ExtractInfo --> KeyPoints[关键要点]
        ExtractInfo --> Entities[实体识别]
        ExtractInfo --> Actions[行动项]
        ExtractInfo --> Preferences[用户偏好]
        ExtractInfo --> Context[上下文信息]
    end
    
    subgraph "输出格式"
        Summary --> FormatJSON[JSON 格式]
        KeyPoints --> FormatJSON
        Entities --> FormatJSON
        Actions --> FormatJSON
        Preferences --> FormatJSON
        Context --> FormatJSON
        
        FormatJSON --> ValidateJSON[验证 JSON]
        ValidateJSON --> ReturnResult[返回结果]
    end
    
    subgraph "质量检查"
        ReturnResult --> CheckQuality[质量检查]
        CheckQuality --> Valid{有效？}
        Valid -->|是 | StoreMem
        Valid -->|否 | RetryExtract[重新提取]
        
        RetryExtract --> ExtractInfo
        StoreMem[存储记忆]
    end
    
    style Start fill:#e1f5ff
    style StoreMem fill:#e1ffe1
    style DefineRole fill:#fff4e1
    style FormatJSON fill:#f0e1ff
    style CheckQuality fill:#ffe1e1
```

## 8. 记忆检索评分图

展示记忆检索的评分和排序机制。

```mermaid
graph TB
    subgraph "初始评分"
        Start[检索查询] --> VectorScore[向量相似度]
        VectorScore --> NormalizeScore[归一化分数]
    end
    
    subgraph "时间衰减"
        NormalizeScore --> GetTime[获取时间差]
        GetTime --> CalcDecay[计算衰减]
        CalcDecay --> TimeScore[时间分数]
    end
    
    subgraph "重要性加权"
        TimeScore --> GetImportance[获取重要性]
        GetImportance --> ApplyWeight[应用权重]
        ApplyWeight --> WeightedScore[加权分数]
    end
    
    subgraph "多样性调整"
        WeightedScore --> CheckSimilarity[检查相似度]
        CheckSimilarity --> Diversify[多样性调整]
        Diversify --> FinalScore[最终分数]
    end
    
    subgraph "排序过滤"
        FinalScore --> SortScores[排序分数]
        SortScores --> FilterLow[过滤低分]
        FilterLow --> SelectTop[选择 Top-K]
    end
    
    subgraph "分数计算"
        VectorScore --> VectorFormula["Vector = cosine_similarity"]
        TimeScore --> TimeFormula["Time = exp(-decay * days_old)"]
        WeightedScore --> WeightFormula["Weighted = Vector * (1 + importance_factor)"]
        FinalScore --> DiversityFormula["Final = Weighted * diversity_factor"]
    end
    
    style Start fill:#e1f5ff
    style SelectTop fill:#e1ffe1
    style VectorScore fill:#fff4e1
    style Diversify fill:#f0e1ff
    style FilterLow fill:#ffe1e1
```

## 图表说明

### 记忆生命周期
1. **创建**: 从对话消息提取
2. **存储**: 保存到数据库和向量库
3. **检索**: 根据查询检索相关记忆
4. **更新**: 定期更新过时记忆
5. **清理**: 删除过期记忆

### 记忆提取
- **摘要生成**: 生成对话摘要
- **关键信息**: 提取关键点
- **实体识别**: 识别人名、地点、组织等
- **行动项**: 提取待办事项
- **偏好**: 识别用户偏好

### 检索机制
- **向量搜索**: 基于嵌入向量相似度
- **时间衰减**: 旧记忆分数降低
- **重要性加权**: 重要记忆权重增加
- **多样性**: 避免相似记忆重复

### 去重策略
- **相似度阈值**: 超过阈值视为重复
- **时间窗口**: 短时间内的相似记忆
- **内容重叠**: 内容重叠度检查
- **智能合并**: 合并相似记忆内容

### 配置参数
- **max_memories**: 最大记忆数量
- **similarity_threshold**: 去重相似度阈值
- **retrieval_top_k**: 检索 Top-K 数量
- **enabled**: 是否启用记忆
- **extraction_config**: 提取配置

### 数据结构
- **id**: 记忆唯一标识
- **thread_id**: 所属线程
- **content**: 记忆内容
- **summary**: 摘要
- **entities**: 实体列表
- **actions**: 行动项
- **importance**: 重要性分数
- **embedding**: 嵌入向量

### 使用场景
- 跨会话上下文保留
- 用户偏好学习
- 对话历史摘要
- 任务跟踪和提醒
- 个性化响应

### 性能优化
1. **批量处理**: 队列批量提取
2. **异步执行**: 非阻塞提取
3. **向量索引**: 高效相似度搜索
4. **缓存机制**: 减少重复计算
5. **定期清理**: 控制存储大小
