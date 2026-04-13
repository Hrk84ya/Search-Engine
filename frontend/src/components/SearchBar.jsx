import React, { useState } from 'react'
import './SearchBar.css'

export default function SearchBar({ onSearch, loading, topK, onTopKChange }) {
  const [query, setQuery] = useState('')
  const [showSettings, setShowSettings] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (query.trim() && !loading) {
      onSearch(query.trim())
    }
  }

  return (
    <form className="search-bar" onSubmit={handleSubmit}>
      <div className="search-input-wrap">
        <span className="search-icon">⌕</span>
        <input
          type="text"
          className="search-input"
          placeholder="Ask anything about your documents..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={loading}
        />
        <button
          type="button"
          className="settings-toggle"
          onClick={() => setShowSettings(!showSettings)}
          title="Search settings"
        >
          ⚙
        </button>
        <button
          type="submit"
          className="search-submit"
          disabled={!query.trim() || loading}
        >
          {loading ? <span className="spinner" /> : '→'}
        </button>
      </div>

      {showSettings && (
        <div className="search-settings fade-in">
          <label className="setting-label">
            <span>Results count</span>
            <div className="setting-control">
              <input
                type="range"
                min="1"
                max="20"
                value={topK}
                onChange={(e) => onTopKChange(Number(e.target.value))}
              />
              <span className="setting-value">{topK}</span>
            </div>
          </label>
        </div>
      )}
    </form>
  )
}
