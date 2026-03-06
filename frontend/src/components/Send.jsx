import { useState, useCallback, useRef } from 'react'
import { uploadText, uploadFile } from '../api.js'
import ProgressBar from './ProgressBar.jsx'
import ErrorMessage from './ErrorMessage.jsx'

const MAX_FILE_SIZE_MB = 50
const MAX_FILE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1048576).toFixed(1)} MB`
}

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
      {expired ? '⏰ Expired' : `⏱ Expires in ${mins}:${secs.toString().padStart(2, '0')}`}
    </span>
  )
}

export default function Send() {
  const [mode, setMode] = useState('text') // 'text' | 'file'
  const [text, setText] = useState('')
  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [progress, setProgress] = useState(0)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null) // { code, expires_in, type }
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)
  const fileInputRef = useRef(null)

  const reset = () => {
    setResult(null)
    setError('')
    setProgress(0)
    setFile(null)
    setText('')
    setCopied(false)
  }

  const handleFileSelect = (f) => {
    if (!f) return
    if (f.size > MAX_FILE_BYTES) {
      setError(`File is too large. Maximum size is ${MAX_FILE_SIZE_MB}MB.`)
      return
    }
    setFile(f)
    setError('')
  }

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) handleFileSelect(f)
  }, [])

  const handleDragOver = (e) => { e.preventDefault(); setDragging(true) }
  const handleDragLeave = () => setDragging(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    setProgress(0)

    try {
      let res
      if (mode === 'text') {
        if (!text.trim()) { setError('Please enter some text to share.'); setLoading(false); return }
        res = await uploadText(text.trim())
      } else {
        if (!file) { setError('Please select a file to upload.'); setLoading(false); return }
        res = await uploadFile(file, setProgress)
      }
      setResult(res)
    } catch (err) {
      setError(err.message || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const copyCode = async () => {
    try {
      await navigator.clipboard.writeText(result.code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback for non-HTTPS
      const el = document.createElement('textarea')
      el.value = result.code
      document.body.appendChild(el)
      el.select()
      document.execCommand('copy')
      document.body.removeChild(el)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  if (result) {
    return (
      <div className="result-card">
        <div className="result-icon">✅</div>
        <h2>Your share code is ready!</h2>
        <div className="code-display">
          <span className="code-value">{result.code}</span>
          <button className="btn btn-copy" onClick={copyCode}>
            {copied ? '✓ Copied!' : '📋 Copy'}
          </button>
        </div>
        <p className="result-hint">Share this code with the recipient. They have 10 minutes to retrieve it.</p>
        <CountdownTimer seconds={result.expires_in} />
        <button className="btn btn-ghost" onClick={reset} style={{ marginTop: '1.5rem' }}>
          Share something else
        </button>
      </div>
    )
  }

  return (
    <form className="send-form" onSubmit={handleSubmit}>
      <div className="mode-toggle">
        <button
          type="button"
          className={`mode-btn ${mode === 'text' ? 'active' : ''}`}
          onClick={() => { setMode('text'); setError('') }}
        >
          📝 Text
        </button>
        <button
          type="button"
          className={`mode-btn ${mode === 'file' ? 'active' : ''}`}
          onClick={() => { setMode('file'); setError('') }}
        >
          📁 File
        </button>
      </div>

      {mode === 'text' ? (
        <textarea
          className="text-input"
          placeholder="Type or paste your text here…"
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={8}
          maxLength={102400}
          disabled={loading}
        />
      ) : (
        <div
          className={`drop-zone ${dragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => !file && fileInputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && !file && fileInputRef.current?.click()}
          aria-label="Drop zone for file upload"
        >
          <input
            ref={fileInputRef}
            type="file"
            className="file-input-hidden"
            onChange={(e) => handleFileSelect(e.target.files[0])}
            accept=".txt,.pdf,.docx,.doc,.png,.jpg,.jpeg,.gif,.webp,.apk,.zip,.csv,.xlsx,.mp4,.mp3"
          />
          {file ? (
            <div className="file-info">
              <span className="file-icon">📄</span>
              <div>
                <div className="file-name">{file.name}</div>
                <div className="file-size">{formatFileSize(file.size)}</div>
              </div>
              <button
                type="button"
                className="btn btn-ghost btn-small"
                onClick={(e) => { e.stopPropagation(); setFile(null) }}
              >
                ✕ Remove
              </button>
            </div>
          ) : (
            <div className="drop-hint">
              <span className="drop-icon">☁️</span>
              <p>Drag & drop a file here, or <span className="drop-link">click to browse</span></p>
              <p className="drop-sub">Max {MAX_FILE_SIZE_MB}MB · PDF, DOCX, PNG, JPG, APK, ZIP and more</p>
            </div>
          )}
        </div>
      )}

      {loading && mode === 'file' && progress > 0 && (
        <ProgressBar progress={progress} />
      )}

      <ErrorMessage message={error} onDismiss={() => setError('')} />

      <button
        type="submit"
        className="btn btn-primary"
        disabled={loading || (mode === 'text' ? !text.trim() : !file)}
      >
        {loading ? (mode === 'file' ? `Uploading… ${progress}%` : 'Sharing…') : '🚀 Share'}
      </button>
    </form>
  )
}
