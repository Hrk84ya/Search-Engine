import React, { useState } from 'react'
import Header from './components/Header'
import SearchBar from './components/SearchBar'
import ResultsPanel from './components/ResultsPanel'
import UploadModal from './components/UploadModal'
import HealthBadge from './components/HealthBadge'
import './App.css'

const API_URL = 'http://localhost:8000'

export default function App() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showUpload, setShowUpload] = useState(false)
  const [topK, setTopK] = useState(5)

  const handleSearch = async (query) => {
    setLoading(true)
    setError(null)
    setResults(null)
    try {
      const res = await fetch(`${API_URL}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: topK }),
      })
      if (!res.ok) throw new Error(`Search failed (${res.status})`)
      const data = await res.json()
      setResults(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <Header onUploadClick={() => setShowUpload(true)} />
      <main className="main">
        <section className="hero">
          <h1 className="hero-title">
            Find answers, <span className="hero-accent">not just links.</span>
          </h1>
          <p className="hero-sub">
            Semantic search powered by AI — understands meaning, returns context-aware answers.
          </p>
          <SearchBar
            onSearch={handleSearch}
            loading={loading}
            topK={topK}
            onTopKChange={setTopK}
          />
        </section>

        {error && (
          <div className="error-banner fade-in">
            <span className="error-icon">⚠</span>
            {error}
          </div>
        )}

        {loading && <LoadingSkeleton />}

        {results && !loading && (
          <ResultsPanel results={results} />
        )}

        {!results && !loading && !error && (
          <EmptyState />
        )}
      </main>

      <footer className="footer">
        <HealthBadge apiUrl={API_URL} />
        <span className="footer-text">Semantic Search Engine · RAG Pipeline</span>
      </footer>

      {showUpload && (
        <UploadModal
          apiUrl={API_URL}
          onClose={() => setShowUpload(false)}
        />
      )}
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="skeleton-container fade-in">
      <div className="skeleton-answer">
        <div className="skeleton-line w80" />
        <div className="skeleton-line w60" />
        <div className="skeleton-line w90" />
      </div>
      {[1, 2, 3].map(i => (
        <div key={i} className="skeleton-card">
          <div className="skeleton-line w40" />
          <div className="skeleton-line w100" />
          <div className="skeleton-line w70" />
        </div>
      ))}
    </div>
  )
}

function EmptyState() {
  return (
    <div className="empty-state fade-in">
      <div className="empty-icon">◎</div>
      <h3>Ready to search</h3>
      <p>Upload documents and ask questions in natural language.</p>
      <div className="empty-hints">
        <span className="hint-chip">What is machine learning?</span>
        <span className="hint-chip">Explain Kubernetes pods</span>
        <span className="hint-chip">How does RAG work?</span>
      </div>
    </div>
  )
}
