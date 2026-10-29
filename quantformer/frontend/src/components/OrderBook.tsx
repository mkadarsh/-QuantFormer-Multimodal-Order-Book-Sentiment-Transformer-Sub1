import type { OrderBookData, OrderBookLevel } from '../types'

interface OrderBookProps { orderbook: OrderBookData | null }

function levels(levels: OrderBookLevel[], maxVolume: number, kind: 'ask' | 'bid') {
  return levels.slice(0, 8).map((level) => (
    <div className={`book-row ${kind}`} key={`${kind}-${level.price}`}>
      <span>{level.price.toFixed(2)}</span>
      <span className="book-volume">{level.volume.toFixed(2)}</span>
      <span className="depth-bar" style={{ width: `${Math.max(3, (level.volume / maxVolume) * 100)}%` }} />
    </div>
  ))
}

export default function OrderBook({ orderbook }: OrderBookProps) {
  if (!orderbook) return <section className="panel orderbook-panel"><div className="card-heading"><div><span className="eyebrow">Liquidity</span><h2>Order book</h2></div></div><div className="empty-state">Waiting for order book data…</div></section>
  const maxVolume = Math.max(...orderbook.bids.concat(orderbook.asks).map((level) => level.volume), 1)
  return (
    <section className="panel orderbook-panel">
      <div className="card-heading"><div><span className="eyebrow">Liquidity</span><h2>Order book</h2></div><span className="spread-pill">Spread {orderbook.spread.toFixed(3)}</span></div>
      <div className="book-header"><span>Price</span><span>Size</span></div>
      <div className="book-levels asks">{levels(orderbook.asks, maxVolume, 'ask')}</div>
      <div className="mid-price"><span>Last traded</span><strong>{orderbook.last_price.toFixed(2)}</strong></div>
      <div className="book-levels bids">{levels(orderbook.bids, maxVolume, 'bid')}</div>
      <div className="book-totals"><span><i className="legend-dot bid-dot" />Bid {orderbook.bid_volume_total.toFixed(1)}</span><span><i className="legend-dot ask-dot" />Ask {orderbook.ask_volume_total.toFixed(1)}</span></div>
    </section>
  )
}
