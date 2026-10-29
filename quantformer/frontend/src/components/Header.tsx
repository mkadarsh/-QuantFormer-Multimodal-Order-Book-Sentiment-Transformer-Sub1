import type { ConnectionStatus, ModelStatus } from '../types'

interface HeaderProps {
  symbol: string
  connectionStatus: ConnectionStatus
  modelStatus: ModelStatus | null
  tickCount: number
  lastTickAt: Date | null
}

export default function Header({ symbol, connectionStatus, modelStatus, tickCount, lastTickAt }: HeaderProps) {
  const statusLabel = connectionStatus === 'live' ? 'Live' : connectionStatus === 'connecting' ? 'Connecting' : 'Offline'

  return (
    <header className="topbar">
      <div className="brand">
        <div className="brand-mark" aria-hidden="true">Q</div>
        <div>
          <div className="brand-name">QuantFormer</div>
          <div className="brand-subtitle">Multimodal market intelligence</div>
        </div>
      </div>
      <div className="header-meta">
        <span className="symbol-pill">{symbol}</span>
        <span className={`connection-pill connection-${connectionStatus}`}>
          <span className="status-dot" aria-hidden="true" />
          {statusLabel}
        </span>
        <span className="stream-pill">{tickCount > 0 ? `${tickCount} ticks · ${lastTickAt?.toLocaleTimeString()}` : 'Awaiting stream'}</span>
        <span className={`connection-pill connection-${modelStatus?.loaded ? 'live' : 'offline'}`}>
          MODEL: {modelStatus?.model ?? '—'} · {modelStatus?.loaded ? 'MODEL LOADED' : 'MODEL NOT AVAILABLE'}
        </span>
      </div>
    </header>
  )
}
