

const BASE = ''


export async function sendMessage(sessionId, message, onEvent) {
  const resp = await fetch(`${BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
  })
  if (!resp.ok || !resp.body) throw new Error(`请求失败：${resp.status}`)

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const frames = buffer.split('\n\n')
    buffer = frames.pop()
    for (const frame of frames) {
      const line = frame.split('\n').find((l) => l.startsWith('data: '))
      if (line) onEvent(JSON.parse(line.slice(6)))
    }
  }
}

export const fetchStats = () => fetch(`${BASE}/api/admin/stats`).then((r) => r.json())

export const fetchHistory = (sessionId) =>
  fetch(`${BASE}/api/history/${sessionId}`).then((r) => r.json())
