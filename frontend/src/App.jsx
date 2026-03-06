import { useState } from 'react'
import Send from './components/Send.jsx'
import Receive from './components/Receive.jsx'

export default function App() {
  const [tab, setTab] = useState('send')

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo">
          <span className="logo-icon">⚡</span>
          <span className="logo-text">QuickShare</span>
        </div>
        <p className="tagline">Share files & text instantly · Auto-expires in 10 minutes</p>
      </header>

      <main className="app-main">
        <div className="card">
          <div className="tab-bar">
            <button
              className={`tab-btn ${tab === 'send' ? 'active' : ''}`}
              onClick={() => setTab('send')}
            >
              📤 Send
            </button>
            <button
              className={`tab-btn ${tab === 'receive' ? 'active' : ''}`}
              onClick={() => setTab('receive')}
            >
              📥 Receive
            </button>
          </div>

          <div className="tab-content">
            {tab === 'send' ? <Send /> : <Receive />}
          </div>
        </div>
      </main>

      <footer className="app-footer">
        <p>Shares are deleted after 10 minutes · No account needed · End-to-end simplicity</p>
      </footer>
    </div>
  )
}
