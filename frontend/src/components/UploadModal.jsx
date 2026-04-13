import React, { useState, useRef } from 'react'
import './UploadModal.css'

export default function UploadModal({ apiUrl, onClose }) {
  const [file, setFile] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const inputRef = useRef()

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const f = e.dataTransfer.files[0]
    if (f) setFile(f)
  }

  const handleUpload = async () => {
    if (!file) return
    setUploading(true)
    setError(null)
    setResult(null)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await fetch(`${apiUrl}/upload`, { method: 'POST', body: form })
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || `Upload failed (${res.status})`)
      }
      setResult(await res.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setUploading(false)
    }
  }

  const fileExt = file?.name?.split('.').pop()?.toLowerCase()
  const fileIcon = { pdf: '📕', txt: '📄', docx: '📘' }[fileExt] || '📎'

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content fade-in" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Upload Document</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div
          className={`drop-zone ${dragOver ? 'drag-over' : ''} ${file ? 'has-file' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.txt,.docx"
            hidden
            onChange={(e) => setFile(e.target.files[0])}
          />
          {file ? (
            <div className="file-preview">
              <span className="file-icon">{fileIcon}</span>
              <div className="file-info">
                <span className="file-name">{file.name}</span>
                <span className="file-size">{(file.size / 1024).toFixed(1)} KB</span>
              </div>
              <button className="file-remove" onClick={(e) => { e.stopPropagation(); setFile(null); setResult(null) }}>✕</button>
            </div>
          ) : (
            <div className="drop-prompt">
              <span className="drop-icon">↑</span>
              <p>Drop a file here or click to browse</p>
              <span className="drop-formats">PDF, TXT, DOCX</span>
            </div>
          )}
        </div>

        {error && <div className="upload-error">{error}</div>}

        {result && (
          <div className="upload-success fade-in">
            <span className="success-icon">✓</span>
            <div>
              <strong>{result.message}</strong>
              <p className="success-detail">
                {result.chunk_count} chunks indexed · ID: {result.document_id.slice(0, 8)}…
              </p>
            </div>
          </div>
        )}

        <div className="modal-actions">
          <button className="btn-secondary" onClick={onClose}>
            {result ? 'Done' : 'Cancel'}
          </button>
          {!result && (
            <button
              className="btn-primary"
              onClick={handleUpload}
              disabled={!file || uploading}
            >
              {uploading ? 'Indexing…' : 'Upload & Index'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
