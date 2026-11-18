
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from ..config import settings
from ..rag.retriever import get_retriever
from ..tools.orders import query_logistics, query_order, refund_policy

llm = ChatOpenAI(
    model=settings.llm_model,
    api_key=settings.api_key,
    base_url=settings.llm_base_url,
    temperature=0.2,
)

TOOLS = [query_order, query_logistics, refund_policy]


_retriever = None


def _get_retriever():
    global _retriever
    if _retriever is None:
        _retriever = get_retriever(k=settings.retrieval_k)
    return _retriever


class IntentResult(BaseModel):
    label: str = Field(description="意图标签：faq / tool / chitchat / human")
    confidence: float = Field(description="判断置信度，0~1 之间的浮点数")


intent_llm = llm.with_structured_output(IntentResult)

INTENT_SYSTEM = """你是电商智能客服的路由模块。根据对话历史和用户最新消息判断意图，只能输出以下四类之一：
- faq：咨询知识类问题（退货政策、配送范围、会员规则、发票等）
- tool：需要查询系统数据的请求（订单状态、物流进度、退款进度）
- chitchat：问候、闲聊、与业务无关的话题
- human：用户明确要求人工客服，或出现明显负面情绪、投诉
"""


def intent_node(state: dict) -> dict:
    history_text = "\n".join(
        f"{m['role']}: {m['content']}" for m in state.get("history", [])
    )
    result = intent_llm.invoke(
        [
            SystemMessage(content=INTENT_SYSTEM),
            HumanMessage(
                content=f"对话历史：\n{history_text or '（无）'}\n\n用户最新消息：{state['question']}"
            ),
        ]
    )
    return {"intent": result.label, "confidence": float(result.confidence)}


def route(state: dict) -> str:

    if state["intent"] == "human":
        return "handoff"
    if state["confidence"] < settings.handoff_confidence_threshold:
        return "handoff"
    return state["intent"]


FAQ_SYSTEM = """你是电商智能客服助手。只能依据下面提供的【知识库内容】回答用户问题：
1. 不要编造知识库中没有的信息；
2. 若知识库信息不足以回答，明确说明并建议转人工客服；
3. 回答简洁友好，末尾用【来源】标注你使用的内容来自哪个章节。"""


def faq_node(state: dict) -> dict:
    docs = _get_retriever().invoke(state["question"])
    context = "\n\n".join(
        f"[片段{i + 1} | {d.metadata.get('section', '')}]\n{d.page_content}"
        for i, d in enumerate(docs)
    )
    answer = llm.invoke(
        [
            SystemMessage(content=FAQ_SYSTEM),
            HumanMessage(content=f"知识库内容：\n{context}\n\n用户问题：{state['question']}"),
        ]
    ).content
    sources = [d.metadata.get("section", "未知来源") for d in docs]
    return {"answer": answer, "sources": sources}


def tool_node(state: dict) -> dict:

    response = llm.bind_tools(TOOLS).invoke(
        [HumanMessage(content=state["question"])]
    )
    observations = []
    for tc in response.tool_calls or []:
        for t in TOOLS:
            if t.name == tc["name"]:
                observations.append((t.name, t.invoke(tc["args"])))
    if not observations:

        return {"answer": response.content, "sources": []}

    obs_text = "\n".join(f"{name} 返回：{result}" for name, result in observations)
    answer = llm.invoke(
        [
            SystemMessage(content="你是电商客服，请根据工具查询结果，用简洁友好的中文回复用户。"),
            HumanMessage(
                content=f"用户问题：{state['question']}\n\n工具查询结果：\n{obs_text}"
            ),
        ]
    ).content
    return {"answer": answer, "sources": [name for name, _ in observations]}


CHITCHAT_SYSTEM = "你是友好的电商客服小助手，进行轻松简短的日常寒暄，回答控制在两三句话内。"


def chitchat_node(state: dict) -> dict:
    history_text = "\n".join(
        f"{m['role']}: {m['content']}" for m in state.get("history", [])
    )
    answer = llm.invoke(
        [
            SystemMessage(content=CHITCHAT_SYSTEM),
            HumanMessage(content=f"对话历史：\n{history_text or '（无）'}\n\n用户消息：{state['question']}"),
        ]
    ).content
    return {"answer": answer, "sources": []}


def handoff_node(state: dict) -> dict:
    reason = (
        "用户要求或情绪原因"
        if state.get("intent") == "human"
        else f"意图识别置信度不足（{state.get('confidence', 0):.2f}）"
    )
    return {
        "handoff": True,
        "answer": f"抱歉没能帮到您（原因：{reason}）。已为您接入人工客服，请稍候，"
        "工作时间（9:00-21:00）内预计 1 分钟内响应。",
        "sources": [],
    }
