# SmartSupport · 智能客服 Agent 平台

基于 **LangGraph + RAG + Function Calling** 的全链路智能客服系统。用户提问后由意图识别节点分流到不同处理分支，覆盖 Agent 应用开发的核心工程能力：条件路由、检索增强、工具调用、多轮记忆、SSE 流式输出与效果评估。

## 核心能力

- **多意图条件路由**：意图识别节点输出意图与置信度，通过 `add_conditional_edges` 分流到 FAQ / 工具 / 闲聊 / 转人工四条分支
- **RAG 检索增强**：Chroma 向量库 + BGE 中文 embedding，知识库检索后带引用生成回答
- **Function Calling**：订单查询、物流跟踪、退款申请三个 Mock 业务工具
- **分层记忆**：SQLite 持久化会话历史 + 用户画像
- **SSE 流式输出**：后端流式推送回答，前端实时渲染
- **管理后台**：意图分布、转人工率等运营指标接口
- **效果评估**：ragas + ranx 检索与生成质量评估流水线

## 架构

```
接入层    React 聊天窗口（SSE 流式） · 管理后台看板
             │
服务层    FastAPI  /api/chat(SSE)  /api/history  /api/admin/stats  /api/health
             │
编排层    LangGraph StateGraph
          intent（意图识别 + 置信度）
             └─ 条件路由
                ├─ faq      → RAG 检索 + 带引用回答
                ├─ tool     → Function Calling（订单/物流/退款）
                ├─ chitchat → 带历史的多轮闲聊
                └─ handoff  → 低置信度转人工
             │
能力层    Chroma 向量库 · BGE embedding · SQLite 记忆 · Mock 业务工具
基础设施  DeepSeek API · Docker
```

## 快速启动

后端：

```bash
cd backend
copy .env.example .env        # 填入 DEEPSEEK_API_KEY
pip install -r requirements.txt
python -m app.rag.ingest      # 首次运行需下载 BGE 模型
uvicorn app.main:app --reload --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

Docker 一键启动：

```bash
DEEPSEEK_API_KEY=sk-xxx docker compose up --build
```

## 目录结构

```
smart-support/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI：SSE 流式 + 统计接口
│   │   ├── config.py          # 配置（.env）
│   │   ├── graph/             # LangGraph：state / nodes / build
│   │   ├── rag/               # ingest 入库 / retriever 检索
│   │   ├── tools/             # Mock 业务工具 + @tool 定义
│   │   ├── memory/            # SQLite 会话历史 + 用户画像
│   │   └── eval/              # ragas + ranx 评估
│   └── data/kb/faq.md         # 示例知识库
└── frontend/                  # Vite + React 聊天窗 + 管理后台
```

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | React · Vite · SSE |
| 服务 | FastAPI · uvicorn |
| Agent 编排 | LangGraph（StateGraph + 条件边） |
| 检索 | Chroma · HuggingFace BGE embedding |
| LLM | DeepSeek（ChatOpenAI 兼容接口） |
| 存储 | SQLite（会话记忆） |
| 评估 | ragas · ranx |
| 部署 | Docker · docker-compose |

## 环境要求

- Python 3.10+
- Node.js 18+
- `DEEPSEEK_API_KEY`（见 `backend/.env.example`）
