import type { SentimentData } from '../types'

interface SentimentCardProps { sentiment: SentimentData | null }

export default function SentimentCard({ sentiment }: SentimentCardProps) {
  const value = sentiment?.normalized_score ?? 0
  const label = sentiment?.sentiment ?? 'neutral'
  const position = `${((value + 1) / 2) * 100}%`
  return (
    <section className="panel sentiment-card">
      <div className="card-heading"><div><span className="eyebrow">NLP signal</span><h2>Sentiment</h2></div><span className={`sentiment-label ${label.toLowerCase()}`}>{label}</span></div>
      <div className="sentiment-score"><strong>{sentiment ? (value > 0 ? '+' : '') + value.toFixed(2) : '—'}</strong><span>normalized score</span></div>
      <div className="sentiment-scale"><span>Bearish</span><div className="sentiment-track"><div className="sentiment-marker" style={{ left: position }} /></div><span>Bullish</span></div>
      <p className="sentiment-headline">{sentiment?.headline ?? 'News sentiment will appear with the next update.'}</p>
      <span className="metric-label">{sentiment?.source === 'finbert' ? 'FINBERT' : 'SENTIMENT FALLBACK'}</span>
    </section>
  )
}
