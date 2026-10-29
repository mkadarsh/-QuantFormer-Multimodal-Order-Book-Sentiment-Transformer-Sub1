interface ConfidenceRangeProps {
  lowerBound: number
  upperBound: number
  currentPrice: number
  predictedPrice: number
}

export default function ConfidenceRange({ lowerBound, upperBound, currentPrice, predictedPrice }: ConfidenceRangeProps) {
  const range = Math.max(upperBound - lowerBound, 0.01)
  const currentPosition = Math.min(100, Math.max(0, ((currentPrice - lowerBound) / range) * 100))
  const predictedPosition = Math.min(100, Math.max(0, ((predictedPrice - lowerBound) / range) * 100))

  return (
    <div className="confidence-range">
      <div className="range-labels"><span>Confidence range</span><span>{lowerBound.toFixed(2)} — {upperBound.toFixed(2)}</span></div>
      <div className="range-track" aria-label={`Confidence range from ${lowerBound} to ${upperBound}`}>
        <div className="range-fill" />
        <span className="range-marker current-marker" style={{ left: `${currentPosition}%` }} title="Current price" />
        <span className="range-marker predicted-marker" style={{ left: `${predictedPosition}%` }} title="Predicted price" />
      </div>
      <div className="range-legend"><span><i className="legend-dot current-dot" />Current {currentPrice.toFixed(2)}</span><span><i className="legend-dot predicted-dot" />Forecast {predictedPrice.toFixed(2)}</span></div>
    </div>
  )
}
