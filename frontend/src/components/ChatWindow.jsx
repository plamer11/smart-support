import { useEffect, useRef, useState } from 'react'
import { sendMessage } from '../api.js'

const INTENT_LABEL = {
  faq: '知识问答',
  tool: '工具调用',
  chitchat: '闲聊',
  human: '转人工',
}

const SUGGESTIONS = [
  '你们的退货政策是什么？',
  '订单 A1001 到哪了？',
  '积分有什么用？',
  '我要投诉，转人工！',
]

let seq = 0

export default function ChatWindow() {
  const [sessionId, setSessionId] = useState(() => `s-${Date.now().toString(36)}`)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const boxRef = useRef(null)

  useEffect(() => {
    boxRef.current?.scrollTo({ top: boxRef.current.scrollHeight })
  }, [messages])

  const send = async (text) => {
    const message = (text ?? input).trim()
    if (!message || busy) return
    setInput('')
    setBusy(true)
    setMessages((prev) => [...prev, { role: 'user', content: message }])

    const assistant = { role: 'assistant', content: '', intent: null, confidence: null, sources: [], handoff: false }
    setMessages((prev) => [...prev, assistant])

    const patch = (fn) =>
      setMessages((prev) => {
        const copy = [...prev]
        copy[copy.length - 1] = fn(copy[copy.length - 1])
        return copy
      })

    try {
      await sendMessage(sessionId, message, (ev) => {
        if (ev.type === 'token') {
          patch((m) => ({ ...m, content: m.content + ev.content }))
        } else if (ev.type === 'intent') {
          patch((m) => ({ ...m, intent: ev.intent, confidence: ev.confidence }))
        } else if (ev.type === 'final') {
          patch((m) => ({ ...m, sources: ev.sources || [], handoff: !!ev.handoff }))
        } else if (ev.type === 'error') {
          patch((m) => ({ ...m, content: m.content + `\n[出错] ${ev.message}` }))
        }
      })
    } catch (e) {
      patch((m) => ({ ...m, content: m.content + `\n[连接失败] ${e.message}` }))
    } finally {
      setBusy(false)
    }
  }

  const newSession = () => {
    setSessionId(`s-${Date.now().toString(36)}-${++seq}`)
    setMessages([])
  }

  return (
    <div className="card">
      <div className="session-bar">
        <span>会话：{sessionId}</span>
        <button onClick={newSession}>开启新会话</button>
      </div>
      <div className="chat-box" ref={boxRef}>
        {messages.length === 0 && (
          <div className="empty">
            <p>你好，我是智能客服助手，可以问我：</p>
            {SUGGESTIONS.map((s) => (
              <p key={s}>
                <button onClick={() => send(s)} style={{ border: 'none', background: 'none', color: 'var(--primary)', cursor: 'pointer', padding: 2 }}>
                  {s}
                </button>
              </p>
            ))}
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            {m.content || (m.role === 'assistant' && busy ? '…' : '')}
            {m.role === 'assistant' && (m.intent || m.sources?.length > 0 || m.handoff) && (
              <div className="meta">
                {m.intent && (
                  <span className={`badge ${m.handoff ? 'warn' : ''}`}>
                    {INTENT_LABEL[m.intent] ?? m.intent}
                    {m.confidence != null ? ` · ${m.confidence}` : ''}
                  </span>
                )}
                {m.sources.map((s, j) => (
                  <span key={j} className="badge src">来源：{s}</span>
                ))}
                {m.handoff && <span className="badge warn">已转人工</span>}
              </div>
            )}
          </div>
        ))}
      </div>
      <div className="chat-input">
        <input
          value={input}
          placeholder="输入消息，回车发送"
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          disabled={busy}
        />
        <button onClick={() => send()} disabled={busy || !input.trim()}>
          发送
        </button>
      </div>
    </div>
  )
}
