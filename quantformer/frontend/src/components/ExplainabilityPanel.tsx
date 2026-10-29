import type { ExplanationData } from '../types'

interface ExplainabilityPanelProps { explanation: ExplanationData | null }

const labels: Record<string, string> = { news_sentiment: 'News Sentiment', order_book_imbalance: 'Order Book Imbalance', price_momentum: 'Price Momentum', liquidity: 'Liquidity' }

export default function ExplainabilityPanel({ explanation }: ExplainabilityPanelProps) {
  const contributions = explanation?.feature_contributions ?? {}
  const entries = Object.entries(contributions)
  const max = Math.max(...entries.map(([, value]) => Math.abs(value)), 0.01)
  return (
    <section className="panel explainability-panel">
      <div className="card-heading"><div><span className="eyebrow">MODEL EXPLANATION</span><h2>Why this forecast?</h2></div><span className="explain-label">{explanation?.label ?? 'Signal Contribution Estimate'}</span></div>
      <p className="explanation-text">{explanation?.human_readable_explanation ?? explanation?.explanation_text ?? explanation?.message ?? 'Explanation will appear when model signals are available.'}</p>
      {entries.length > 0 && <div className="contribution-list">{entries.map(([key, value]) => <div className="contribution-row" key={key}><div className="contribution-meta"><span>{labels[key] ?? key.replace(/_/g, ' ')}</span><strong className={value >= 0 ? 'positive' : 'negative'}>{value >= 0 ? '+' : ''}{value.toFixed(2)}</strong></div><div className="contribution-track"><span className={value >= 0 ? 'contribution-positive' : 'contribution-negative'} style={{ width: `${Math.max(4, (Math.abs(value) / max) * 100)}%` }} /></div></div>)}</div>}
      {explanation?.tft_attention && <div className="tft-attention"><h3>TFT Attention</h3>{Object.entries(explanation.tft_attention).map(([key, value]) => <div key={key}>{key}: {value.toFixed(3)}</div>)}</div>}
      <div className="risk-note"><span className={`risk-dot risk-${(explanation?.risk_signal ?? 'normal').toLowerCase()}`} />Risk signal: <strong>{(explanation?.risk_signal ?? 'NORMAL').replace('_', ' ')}</strong></div>
    </section>
  )
}
