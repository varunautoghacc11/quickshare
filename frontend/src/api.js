const API_BASE = import.meta.env.VITE_API_URL || ''

/**
 * Share plain text. Returns { code, expires_in, type }
 */
export async function uploadText(text) {
  const res = await fetch(`${API_BASE}/api/share/text`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, type: 'text' }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

/**
 * Upload a file with progress callback. Returns { code, expires_in, type }
 */
export function uploadFile(file, onProgress) {
  return new Promise((resolve, reject) => {
    const formData = new FormData()
    formData.append('file', file)

    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${API_BASE}/api/share/file`)

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText))
        } catch {
          reject(new Error('Invalid server response'))
        }
      } else {
        try {
          const err = JSON.parse(xhr.responseText)
          reject(new Error(err.detail || `Upload failed (${xhr.status})`))
        } catch {
          reject(new Error(`Upload failed (${xhr.status})`))
        }
      }
    }

    xhr.onerror = () => reject(new Error('Network error during upload'))
    xhr.ontimeout = () => reject(new Error('Upload timed out'))

    xhr.send(formData)
  })
}

/**
 * Retrieve share metadata by code. Returns RetrieveResponse.
 */
export async function retrieve(code) {
  const res = await fetch(`${API_BASE}/api/receive/${code}`)
  if (res.status === 404) {
    const err = await res.json().catch(() => ({ detail: 'Code not found or expired' }))
    throw new Error(err.detail || 'Code not found or expired')
  }
  if (res.status === 422) {
    throw new Error('Code must be exactly 6 digits')
  }
  if (res.status === 429) {
    throw new Error('Too many requests — please wait a moment')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

/**
 * Returns the full download URL for a file share.
 */
export function getDownloadUrl(code) {
  return `${API_BASE}/api/receive/${code}/download`
}
