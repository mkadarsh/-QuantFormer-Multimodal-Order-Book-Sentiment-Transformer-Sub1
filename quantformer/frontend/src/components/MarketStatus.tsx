import type { ConnectionStatus, MarketData } from '../types'

interface MarketStatusProps {
  market: MarketData | null
  connectionStatus: ConnectionStatus
  tickCount: number
  lastTickAt: Date | null
}

function formatPrice(value: number | undefined): string {
  return value === undefined ? '—' : value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export default function MarketStatus({ market, connectionStatus, tickCount, lastTickAt }: MarketStatusProps) {
  const change = market?.price_change_pct ?? 0
  const changeClass = change > 0 ? 'positive' : change < 0 ? 'negative' : 'muted'
  const updated = market?.timestamp ? new Date(market.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : 'Waiting for data'

  return (
    <section className="market-status panel">
      <div className="market-heading">
        <div>
          <span className="eyebrow">Market overview</span>
          <h1>{market?.symbol ?? 'DEMO'} <span className="market-open">● OPEN</span></h1>
        </div>
        <span className={`connection-label connection-${connectionStatus}`}>
          <span className="pulse-dot" aria-hidden="true" /> {connectionStatus === 'live' ? 'Streaming' : connectionStatus}
        </span>
      </div>
      <div className="quote-grid">
        <div className="quote-primary">
          <span className="metric-label">Last price</span>
          <strong>{formatPrice(market?.last_price)}</strong>
          <span className={`price-change ${changeClass}`}>{change >= 0 ? '▲' : '▼'} {Math.abs(change).toFixed(2)}%</span>
        </div>
        <div className="quote-stat"><span className="metric-label">Bid</span><strong>{formatPrice(market?.bid)}</strong></div>
        <div className="quote-stat"><span className="metric-label">Ask</span><strong>{formatPrice(market?.ask)}</strong></div>
        <div className="quote-stat"><span className="metric-label">Volume</span><strong>{market?.volume?.toLocaleString(undefined, { maximumFractionDigits: 1 }) ?? '—'}</strong></div>
      </div>
      <div className="updated-at">
        Last update {updated} · <strong>{tickCount}</strong> stream ticks
        {lastTickAt && <span className="stream-latency"> · live feed active</span>}
      </div>
    </section>
  )
}
