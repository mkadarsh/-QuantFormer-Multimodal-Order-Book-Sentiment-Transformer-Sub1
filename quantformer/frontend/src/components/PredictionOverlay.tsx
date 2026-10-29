import type { PredictionData } from '../types'

interface PredictionOverlayProps {
  prediction: PredictionData | null
}

export default function PredictionOverlay({ prediction }: PredictionOverlayProps) {
  if (!prediction) return null
  const direction = prediction.direction.toUpperCase()
  return (
    <div className={`prediction-overlay overlay-${direction.toLowerCase()}`}>
      <span className="overlay-label">Forecast</span>
      <strong>{prediction.predicted_price.toFixed(2)}</strong>
      <span>{Math.round(prediction.confidence * 100)}% confidence</span>
    </div>
  )
}
