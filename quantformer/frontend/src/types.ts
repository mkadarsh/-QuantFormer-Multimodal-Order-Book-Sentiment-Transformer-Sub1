export type ConnectionStatus = 'connecting' | 'live' | 'offline'

export interface MarketData {
  symbol: string
  timestamp: string
  last_price: number
  bid: number
  ask: number
  volume: number
  price_change: number
  price_change_pct: number
}

export interface PricePoint {
  symbol: string
  timestamp: string
  last_price: number
  bid?: number
  ask?: number
  volume?: number
  price_change?: number
  price_change_pct?: number
}

export interface OrderBookLevel {
  price: number
  volume: number
}

export interface OrderBookData {
  symbol: string
  timestamp: string
  last_price: number
  bids: OrderBookLevel[]
  asks: OrderBookLevel[]
  bid_volume_total: number
  ask_volume_total: number
  spread: number
}

export interface NewsItem {
  id: string
  timestamp: string
  headline: string
  source: string
  symbol: string
  sentiment?: string | null
  sentiment_score?: number | null
}

export interface SentimentData {
  symbol: string
  timestamp: string
  sentiment: string
  score: number
  normalized_score: number
  headline?: string | null
  source?: string | null
}

export interface PredictionData {
  symbol: string
  timestamp: string
  current_price: number
  predicted_price: number
  direction: 'UP' | 'DOWN' | 'NEUTRAL' | string
  confidence: number
  lower_bound: number
  upper_bound: number
  risk_level?: string | null
  risk_signal?: string | null
}

export interface ExplanationData {
  prediction?: PredictionData
  risk_level?: string
  explanation_text?: string
  human_readable_explanation?: string
  feature_contributions?: Record<string, number>
  risk_signal?: string
  label?: string
  status?: string
  message?: string
  tft_attention?: Record<string, number>
}

export interface MarketSnapshot {
  type?: string
  timestamp?: string
  market?: MarketData | null
  orderbook?: OrderBookData | null
  news?: NewsItem | null
  sentiment?: SentimentData | null
  prediction?: PredictionData | null
  model?: ModelStatus
  sentiment_status?: ModelStatus
}

export interface ModelStatus {
  model: string
  loaded: boolean
  available?: boolean
  error?: string | null
}
