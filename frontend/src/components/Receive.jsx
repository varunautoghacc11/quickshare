import { useState } from 'react'
import { retrieve, getDownloadUrl } from '../api.js'
import ErrorMessage from './ErrorMessage.jsx'

function CountdownTimer({ seconds }) {
  const [remaining, setRemaining] = useState(seconds)

  useState(() => {
    if (remaining <= 0) return
    const interval = setInterval(() => {
      setRemaining((prev) => {
        if (prev <= 1) { clearInterval(interval); return 0 }
        return prev - 1
      })
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  const mins = Math.floor(remaining / 60)
  const secs = remaining % 60
  const expired = remaining <= 0

  return (
    <span className={`timer ${remaining < 60 ? 'timer-warning' : ''} ${expired ? 'timer-expired' : ''}`}>
      {expired ? '⏰ This share has expired' : `⏱ Expires in ${mins}:${secs.toString().padStart(2, '0')}`}
    </span>
  )
}

export default function Receive() {
  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  const handleCodeChange = (e) => {
    const val = e.target.value.replace(/\D/g, '').slice(0, 6)
    setCode(val)
    setError('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (code.length !== 6) {
      setError('Please enter a 6-digit code.')
      return
    }
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const data = await retrieve(code)
      setResult(data)
    } catch (err) {
      setError(err.message || 'Failed to retrieve. Please check the code and try again.')
    } finally {
      setLoading(false)
    }
  }

  const copyText = async () => {
    if (!result?.content) return
    try {
      await navigator.clipboard.writeText(result.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      const el = document.createElement('textarea')
      el.value = result.content
      document.body.appendChild(el)
      el.select()
      document.execCommand('copy')
      document.body.removeChild(el)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const reset = () => {
    setResult(null)
    setCode('')
    setError('')
    setCopied(false)
  }

  return (
    <div className="receive-container">
      {!result ? (
        <form className="receive-form" onSubmit={handleSubmit}>
          <label className="code-label" htmlFor="code-input">Enter your 6-digit code</label>
          <input
            id="code-input"
            type="text"
            inputMode="numeric"
            pattern="\d{6}"
            className="code-input"
            placeholder="000000"
            value={code}
            onChange={handleCodeChange}
            maxLength={6}
            autoComplete="off"
            autoFocus
            disabled={loading}
          />
          <ErrorMessage message={error} onDismiss={() => setError('')} />
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || code.length !== 6}
          >
            {loading ? 'Fetching…' : '🔍 Retrieve'}
          </button>
        </form>
      ) : (
        <div className="result-card">
          <CountdownTimer seconds={result.expires_in} />

          {result.type === 'text' ? (
            <div className="text-result">
              <div className="text-result-header">
                <h3>📝 Text Content</h3>
                <button className="btn btn-copy" onClick={copyText}>
                  {copied ? '✓ Copied!' : '📋 Copy'}
                </button>
              </div>
              <pre className="text-content">{result.content}</pre>
            </div>
          ) : (
            <div className="file-result">
              <div className="file-result-icon">📄</div>
              <h3>{result.filename || 'File'}</h3>
              <p className="file-result-hint">Click below to download</p>
              <a
                href={getDownloadUrl(code)}
                download={result.filename}
                className="btn btn-primary"
              >
                ⬇️ Download {result.filename}
              </a>
            </div>
          )}

          <button className="btn btn-ghost" onClick={reset} style={{ marginTop: '1rem' }}>
            ← Retrieve another
          </button>
        </div>
      )}
    </div>
  )
}
