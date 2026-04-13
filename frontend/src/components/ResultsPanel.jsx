import React, { useState } from 'react'
import './ResultsPanel.css'

export default function ResultsPanel({ results }) {
  const { query, generated_answer, retrieved_chunks, latency_ms, model_info } = results

  return (
    <div className="results fade-in">
      {/* Generated Answer */}
      <div className="answer-card">
        <div className="answer-header">
          <span className="answer-badge">AI Answer</span>
          <span className="answer-latency">{latency_ms}ms</span>
        </div>
        <p className="answer-text">{generated_answer}</p>
        <div className="answer-meta">
          <span className="meta-chip">{model_info.embedding_model}</span>
          <span className="meta-chip">{model_info.llm_model}</span>
          <span className="meta-chip">top-{model_info.top_k}</span>
        </div>
      </div>

      {/* Source Chunks */}
      <div className="chunks-section">
        <h3 className="chunks-title">
          Sources
          <span className="chunks-count">{retrieved_chunks.length}</span>
        </h3>
        <div className="chunks-list">
          {retrieved_chunks.map((chunk, i) => (
            <ChunkCard key={chunk.chunk_id} chunk={chunk} index={i} />
          ))}
        </div>
      </div>
    </div>
  )
}

function ChunkCard({ chunk, index }) {
  const [expanded, setExpanded] = useState(false)
  const score = (chunk.similarity_score * 100).toFixed(1)
  const preview = chunk.chunk_text.slice(0, 200)
  const hasMore = chunk.chunk_text.length > 200

  return (
    <div
      className="chunk-card"
      style={{ animationDelay: `${index * 0.08}s` }}
    >
      <div className="chunk-top">
        <div className="chunk-rank">#{index + 1}</div>
        <div className="chunk-score-wrap">
          <div className="chunk-score-bar">
            <div
              className="chunk-score-fill"
              style={{ width: `${score}%` }}
            />
          </div>
          <span className="chunk-score-label">{score}%</span>
        </div>
      </div>
      <p className="chunk-text">
        {expanded ? chunk.chunk_text : preview}
        {hasMore && !expanded && '…'}
      </p>
      <div className="chunk-bottom">
        <span className="chunk-doc-id" title={chunk.document_id}>
          Doc: {chunk.document_id.slice(0, 8)}
        </span>
        <span className="chunk-index">Chunk {chunk.chunk_index}</span>
        {hasMore && (
          <button
            className="chunk-expand"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? 'Show less' : 'Show more'}
          </button>
        )}
      </div>
    </div>
  )
}
