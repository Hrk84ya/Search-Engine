import React, { useState, useEffect } from 'react'
import './HealthBadge.css'

export default function HealthBadge({ apiUrl }) {
  const [status, setStatus] = useState('checking')

  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch(`${apiUrl}/health`, { signal: AbortSignal.timeout(5000) })
        if (res.ok) {
          const data = await res.json()
          setStatus(data.database === 'connected' ? 'healthy' : 'degraded')
        } else {
          setStatus('error')
        }
      } catch {
        setStatus('offline')
      }
    }
    check()
    const interval = setInterval(check, 30000)
    return () => clearInterval(interval)
  }, [apiUrl])

  const labels = {
    checking: 'Checking…',
    healthy: 'All systems go',
    degraded: 'Degraded',
    error: 'API error',
    offline: 'Offline',
  }

  return (
    <div className={`health-badge status-${status}`}>
      <span className="health-dot" />
      <span className="health-label">{labels[status]}</span>
    </div>
  )
}
