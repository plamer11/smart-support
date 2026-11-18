import { useState } from 'react'
import ChatWindow from './components/ChatWindow.jsx'
import AdminDashboard from './components/AdminDashboard.jsx'

export default function App() {
  const [tab, setTab] = useState('chat')

  return (
    <div className="app">
      <div className="app-header">
        <h1>SmartSupport</h1>
        <span>智能客服 Agent 平台 · LangGraph + RAG</span>
      </div>
      <div className="tabs">
        <button className={tab === 'chat' ? 'active' : ''} onClick={() => setTab('chat')}>
          客服对话
        </button>
        <button className={tab === 'admin' ? 'active' : ''} onClick={() => setTab('admin')}>
          管理后台
        </button>
      </div>
      {tab === 'chat' ? <ChatWindow /> : <AdminDashboard />}
    </div>
  )
}
