import React from 'react'
import './Header.css'

export default function Header({ onUploadClick }) {
  return (
    <header className="header">
      <div className="header-inner">
        <div className="header-brand">
          <span className="brand-mark">◈</span>
          <span className="brand-name">Nexus</span>
          <span className="brand-tag">Search</span>
        </div>
        <nav className="header-nav">
          <button className="nav-btn upload-btn" onClick={onUploadClick}>
            <span className="btn-icon">↑</span>
            Upload
          </button>
        </nav>
      </div>
    </header>
  )
}
