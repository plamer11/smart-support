
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .graph.build import graph
from .memory import store

app = FastAPI(title="SmartSupport 智能客服 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

store.init_db()


class ChatRequest(BaseModel):
    session_id: str
    message: str


def sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@app.post("/api/chat")
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    store.touch_profile(req.session_id)
    history = store.get_history(req.session_id)
    inputs = {
        "session_id": req.session_id,
        "question": req.message,
        "history": history,
        "intent": "",
        "confidence": 0.0,
        "answer": "",
        "sources": [],
        "handoff": False,
    }

    async def event_stream():
        final = {"intent": "", "confidence": 0.0, "answer": "", "sources": [], "handoff": False}
        try:
            async for mode, chunk in graph.astream(inputs, stream_mode=["updates", "messages"]):
                if mode == "messages":
                    msg, _meta = chunk
                    content = msg.content
                    if isinstance(content, str) and content:
                        yield sse({"type": "token", "content": content})
                else:
                    for node, update in chunk.items():
                        if not update:
                            continue
                        final.update(update)
                        if node == "intent":
                            yield sse({
                                "type": "intent",
                                "intent": final.get("intent"),
                                "confidence": round(float(final.get("confidence", 0)), 2),
                            })
        except Exception as e:
            yield sse({"type": "error", "message": f"服务内部错误：{e}"})


        store.save_message(req.session_id, "user", req.message)
        store.save_message(
            req.session_id, "assistant", final.get("answer", ""),
            intent=final.get("intent"), handoff=1 if final.get("handoff") else 0,
        )
        yield sse({
            "type": "final",
            "sources": final.get("sources", []),
            "handoff": final.get("handoff", False),
        })

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/history/{session_id}")
async def history(session_id: str):
    return {"session_id": session_id, "messages": store.get_history(session_id, k=100)}


@app.get("/api/admin/stats")
async def admin_stats():
    return store.stats()


@app.get("/api/health")
async def health():
    return {"status": "ok"}
