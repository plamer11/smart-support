# SmartSupport · 智能客服 Agent 平台

求职作品项目：基于 **LangGraph + RAG + Function Calling** 的全链路智能客服系统。
覆盖 Agent 应用开发岗的核心面试考点：多分支条件路由、RAG 检索增强、工具调用、
记忆分层、SSE 流式输出、效果评估与 Docker 部署。

## 架构

```
┌─────────────── 接入层 ───────────────┐
│  聊天窗口（React，SSE 流式渲染）  管理后台（意图分布/转人工率看板）
└──────────────────┬──────────────────┘
┌──────────── 服务层 FastAPI ──────────┐
│  POST /api/chat（SSE）  /api/admin/stats  /api/history
└──────────────────┬──────────────────┘
┌───────── Agent 编排层 LangGraph ─────┐
│  intent（意图识别+置信度）            │
│    └─ 条件路由 branch routing        │
│       ├─ faq ── RAG 检索+带引用回答  │
│       ├─ tool ─ Function Calling     │
│       │        （订单/物流/退款）     │
│       ├─ chitchat ─ 带历史闲聊       │
│       └─ handoff ─ 低置信度转人工     │
└──────────────────┬──────────────────┘
   能力层：Chroma 向量库 · BGE embedding · Mock 工具 · SQLite 记忆
   基础设施：DeepSeek API · Langfuse(计划) · ragas+ranx(计划) · Docker
```

## 快速启动（本地开发）

后端（使用 miniconda llm 环境，**先 activate 再装依赖**）：

```bash
conda activate llm
cd backend
copy .env.example .env      # 填入 DEEPSEEK_API_KEY
pip install -r requirements.txt
python -m app.rag.ingest    # 知识库入库（首次会从 hf-mirror 下载 BGE 模型）
uvicorn app.main:app --reload --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173
```

Docker 一键启动：

```bash
DEEPSEEK_API_KEY=sk-xxx docker compose up --build
```

## 目录结构

```
smartsupport/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI：SSE 流式 + 统计接口
│   │   ├── config.py          # 配置（.env）
│   │   ├── graph/             # LangGraph：state / nodes / build
│   │   ├── rag/               # ingest（入库）/ retriever（检索）
│   │   ├── tools/             # Mock 工具 + @tool 定义
│   │   ├── memory/            # SQLite 短期记忆 + 长期画像
│   │   └── eval/              # ragas + ranx 评估（W4）
│   └── data/kb/faq.md         # 示例知识库
└── frontend/                  # Vite + React 聊天窗 + 管理后台
```

## 5 周里程碑

| 周 | 目标 | 状态 |
|---|---|---|
| W1 | 知识库 pipeline + 意图识别跑通（本骨架已含） | ✅ 骨架完成 |
| W2 | LangGraph 四分支 + 工具调用（本骨架已含） | ✅ 骨架完成 |
| W3 | 扩充测试：多轮指代、低置信度转人工、会话历史 | 待做 |
| W4 | ragas/ranx 评估报告 + Langfuse 追踪接入 | 骨架已备 |
| W5 | Docker 验证 + README 完善 + 简历话术 + 深挖预演 | 待做 |

## 面试深挖预演（提前准备答案）

1. 为什么用 LangGraph 而不是 AgentExecutor？→ 见 `graph/build.py` 顶部注释
2. chunk_size=500/overlap=50 怎么定的？→ 见 `rag/ingest.py` 注释，W4 用评估数据佐证
3. 转人工阈值 0.55 怎么选的？→ 可调参数，W3 用测试集统计准确率/转人工率权衡曲线
4. 多轮上下文怎么管理？→ 短期记忆取近 8 轮注入，超长可做摘要压缩（TODO 标注处）
5. 幻觉怎么缓解？→ RAG 限定知识库 + 引用溯源 + "信息不足建议转人工"约束

## TODO（按里程碑推进）

- [ ] W3：意图识别 Few-shot 样例增强；负面情绪检测触发转人工
- [ ] W4：`python -m app.eval.run_eval` 跑出 ragas 基线；ranx 检索排序评估
- [ ] W4：接入 Langfuse（`CallbackHandler` 挂到 ChatOpenAI 即可全链路追踪）
- [ ] W5：前端生产构建 + nginx 镜像；README 补截图
