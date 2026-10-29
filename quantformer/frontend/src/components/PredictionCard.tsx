import type { PredictionData } from '../types'
import ConfidenceRange from './ConfidenceRange'

interface PredictionCardProps {
  prediction: PredictionData | null
}

export default function PredictionCard({ prediction }: PredictionCardProps) {
  if (!prediction) {
    return <section className="panel prediction-card empty-card"><span className="eyebrow">Model forecast</span><h2>Prediction unavailable</h2><p>Waiting for the next model update.</p></section>
  }
  const direction = prediction.direction.toUpperCase()
  const directionClass = direction === 'UP' ? 'positive' : direction === 'DOWN' ? 'negative' : 'muted'
  const risk = prediction.risk_signal ?? prediction.risk_level ?? 'NORMAL'

  return (
    <section className="panel prediction-card">
      <div className="card-heading"><div><span className="eyebrow">Model forecast</span><h2>Next movement</h2></div><span className={`risk-badge risk-${risk.toLowerCase()}`}>{risk.replace('_', ' ')}</span></div>
      <div className="prediction-main">
        <div className={`direction-icon direction-${direction.toLowerCase()}`} aria-hidden="true">{direction === 'UP' ? '↗' : direction === 'DOWN' ? '↘' : '→'}</div>
        <div><span className="metric-label">Predicted price</span><strong className={directionClass}>{prediction.predicted_price.toFixed(2)}</strong><span className={`direction-text ${directionClass}`}>{direction} signal</span></div>
        <div className="confidence-value"><strong>{Math.round(prediction.confidence * 100)}%</strong><span>confidence</span></div>
      </div>
      <ConfidenceRange lowerBound={prediction.lower_bound} upperBound={prediction.upper_bound} currentPrice={prediction.current_price} predictedPrice={prediction.predicted_price} />
    </section>
  )
}
