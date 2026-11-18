import { useEffect, useState } from 'react'
import { fetchStats } from '../api.js'

const INTENT_LABEL = {
  faq: '知识问答',
  tool: '工具调用',
  chitchat: '闲聊',
  human: '转人工',
  未分类: '未分类',
}

export default function AdminDashboard() {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchStats()
      .then(setStats)
      .catch((e) => setError(`无法连接后端：${e.message}（请确认 uvicorn 已启动）`))
  }, [])

  if (error) return <div className="card"><div className="empty">{error}</div></div>
  if (!stats) return <div className="card"><div className="empty">加载中……</div></div>

  const maxCount = Math.max(...stats.intent_distribution.map((d) => d.count), 1)

  return (
    <div>
      <div className="stats-grid">
        <div className="stat-card">
          <div className="label">会话总数</div>
          <div className="value">{stats.total_sessions}</div>
        </div>
        <div className="stat-card">
          <div className="label">消息总数</div>
          <div className="value">{stats.total_messages}</div>
        </div>
        <div className="stat-card">
          <div className="label">转人工会话</div>
          <div className="value">{stats.handoff_sessions}</div>
        </div>
        <div className="stat-card">
          <div className="label">转人工率</div>
          <div className="value">{(stats.handoff_rate * 100).toFixed(1)}%</div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <strong>意图分布（回答轮次）</strong>
        {stats.intent_distribution.map((d) => (
          <div className="bar-row" key={d.intent}>
            <span className="name">{INTENT_LABEL[d.intent] ?? d.intent}</span>
            <div className="bar" style={{ width: `${(d.count / maxCount) * 70}%` }} />
            <span className="num">
              {d.count} · {(d.ratio * 100).toFixed(0)}%
            </span>
          </div>
        ))}
      </div>

      <div className="card">
        <strong>最近会话消息</strong>
        <table className="recent">
          <thead>
            <tr>
              <th>时间</th>
              <th>会话</th>
              <th>角色</th>
              <th>内容</th>
              <th>意图</th>
            </tr>
          </thead>
          <tbody>
            {stats.recent_messages.map((m, i) => (
              <tr key={i}>
                <td>{m.created_at}</td>
                <td>{m.session_id.slice(0, 10)}</td>
                <td>{m.role === 'user' ? '用户' : '客服'}</td>
                <td className="content">{m.content}</td>
                <td>{INTENT_LABEL[m.intent] ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
