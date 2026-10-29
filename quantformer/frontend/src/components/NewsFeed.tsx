import type { NewsItem } from '../types'

interface NewsFeedProps { news: NewsItem | null }

export default function NewsFeed({ news }: NewsFeedProps) {
  return (
    <section className="panel news-panel">
      <div className="card-heading"><div><span className="eyebrow">Market context</span><h2>Latest news</h2></div><span className="live-indicator">LIVE</span></div>
      {news ? <article className="news-item"><div className="news-source"><span className="source-avatar">{news.source.slice(0, 1).toUpperCase()}</span><span>{news.source}</span><time>{new Date(news.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</time></div><h3>{news.headline}</h3><span className={`news-sentiment ${news.sentiment?.toLowerCase() ?? 'neutral'}`}>{news.sentiment ?? 'Neutral'} {news.sentiment_score !== null && news.sentiment_score !== undefined ? `· ${news.sentiment_score.toFixed(2)}` : ''}</span></article> : <div className="empty-state">Waiting for latest headlines…</div>}
    </section>
  )
}
