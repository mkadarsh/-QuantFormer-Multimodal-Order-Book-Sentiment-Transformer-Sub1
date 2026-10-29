import { useCallback, useEffect, useRef, useState } from 'react'
import axios from 'axios'
import type { ConnectionStatus, ExplanationData, MarketData, MarketSnapshot, ModelStatus, NewsItem, OrderBookData, PredictionData, PricePoint, SentimentData } from './types'
import Header from './components/Header'
import MarketStatus from './components/MarketStatus'
import CandlestickChart from './components/CandlestickChart'
import OrderBook from './components/OrderBook'
import NewsFeed from './components/NewsFeed'
import SentimentCard from './components/SentimentCard'
import PredictionCard from './components/PredictionCard'
import ExplainabilityPanel from './components/ExplainabilityPanel'

const configuredApiBase = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '')
const apiBase = configuredApiBase ?? (window.location.port === '5173' ? 'http://localhost:8000' : '')

export default function Dashboard() {
  const [market, setMarket] = useState<MarketData | null>(null)
  const [history, setHistory] = useState<PricePoint[]>([])
  const [orderbook, setOrderbook] = useState<OrderBookData | null>(null)
  const [news, setNews] = useState<NewsItem | null>(null)
  const [sentiment, setSentiment] = useState<SentimentData | null>(null)
  const [prediction, setPrediction] = useState<PredictionData | null>(null)
  const [explanation, setExplanation] = useState<ExplanationData | null>(null)
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('connecting')
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null)
  const [symbol, setSymbol] = useState('DEMO')
  const [tickCount, setTickCount] = useState(0)
  const [lastTickAt, setLastTickAt] = useState<Date | null>(null)
  const socketRef = useRef<WebSocket | null>(null)
  const reconnectTimerRef = useRef<number | null>(null)
  const reconnectAttemptRef = useRef(0)

  const applySnapshot = useCallback((snapshot: MarketSnapshot) => {
    if (snapshot.market) {
      setMarket(snapshot.market)
      setSymbol(snapshot.market.symbol)
      setHistory((current) => {
        const next = current.concat(snapshot.market as PricePoint)
        const unique = next.filter((point, index, values) => values.findIndex((candidate) => candidate.timestamp === point.timestamp) === index)
        return unique.slice(-100)
      })
    }
    if (snapshot.orderbook) setOrderbook(snapshot.orderbook)
    if (snapshot.news) setNews(snapshot.news)
    if (snapshot.sentiment) setSentiment(snapshot.sentiment)
    if (snapshot.prediction) setPrediction(snapshot.prediction)
    if (snapshot.model) setModelStatus(snapshot.model)
    setTickCount((count) => count + 1)
    setLastTickAt(new Date())
  }, [])

  useEffect(() => {
    let active = true
    const loadInitialData = async () => {
      const results = await Promise.allSettled([
        axios.get<MarketData>(`${apiBase}/api/market/latest`),
        axios.get<OrderBookData>(`${apiBase}/api/orderbook`),
        axios.get<NewsItem>(`${apiBase}/api/news/latest`),
        axios.get<SentimentData>(`${apiBase}/api/sentiment/latest`),
        axios.get<PredictionData>(`${apiBase}/api/prediction/latest`),
        axios.get<{ items: PricePoint[] }>(`${apiBase}/api/history?limit=100`),
        axios.get<ExplanationData>(`${apiBase}/api/explanation`),
      ])
      if (!active) return
      const [marketResult, bookResult, newsResult, sentimentResult, predictionResult, historyResult, explanationResult] = results
      if (marketResult.status === 'fulfilled') { setMarket(marketResult.value.data); setSymbol(marketResult.value.data.symbol) }
      if (bookResult.status === 'fulfilled') setOrderbook(bookResult.value.data)
      if (newsResult.status === 'fulfilled') setNews(newsResult.value.data)
      if (sentimentResult.status === 'fulfilled') setSentiment(sentimentResult.value.data)
      if (predictionResult.status === 'fulfilled') setPrediction(predictionResult.value.data)
      if (historyResult.status === 'fulfilled') setHistory(historyResult.value.data.items)
      if (explanationResult.status === 'fulfilled') setExplanation(explanationResult.value.data)
    }
    void loadInitialData()
    return () => { active = false }
  }, [])

  useEffect(() => {
    let active = true
    const connect = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const configuredUrl = import.meta.env.VITE_WS_URL as string | undefined
      const socketUrl = configuredUrl ?? `${apiBase.replace(/^https?:/, protocol)}/ws/market`
      const socket = new WebSocket(socketUrl)
      socketRef.current = socket
      socket.onopen = () => {
        reconnectAttemptRef.current = 0
        setConnectionStatus('live')
      }
      socket.onmessage = (event: MessageEvent<string>) => {
        try { applySnapshot(JSON.parse(event.data) as MarketSnapshot) } catch { /* Ignore malformed stream messages. */ }
      }
      socket.onerror = () => setConnectionStatus('offline')
      socket.onclose = () => {
        if (!active) return
        setConnectionStatus('offline')
        const delay = Math.min(10000, 1000 * 2 ** reconnectAttemptRef.current)
        reconnectAttemptRef.current += 1
        reconnectTimerRef.current = window.setTimeout(connect, delay)
      }
    }
    connect()
    return () => {
      active = false
      if (reconnectTimerRef.current !== null) window.clearTimeout(reconnectTimerRef.current)
      socketRef.current?.close()
      socketRef.current = null
    }
  }, [applySnapshot])

  useEffect(() => {
    let active = true
    const refreshExplanation = async () => {
      try {
        const response = await axios.get<ExplanationData>(`${apiBase}/api/explanation`)
        if (active) setExplanation(response.data)
      } catch { /* Explanation is optional while the stream is warming up. */ }
    }
    void refreshExplanation()
    const interval = window.setInterval(() => { void refreshExplanation() }, 5000)
    return () => { active = false; window.clearInterval(interval) }
  }, [])

  return (
    <div className="dashboard-shell">
      <Header symbol={symbol} connectionStatus={connectionStatus} modelStatus={modelStatus} tickCount={tickCount} lastTickAt={lastTickAt} />
      <main className="dashboard-content">
        <MarketStatus market={market} connectionStatus={connectionStatus} tickCount={tickCount} lastTickAt={lastTickAt} />
        <div className="dashboard-grid primary-grid">
          <CandlestickChart history={history} prediction={prediction} />
          <OrderBook orderbook={orderbook} />
        </div>
        <div className="dashboard-grid signal-grid">
          <PredictionCard prediction={prediction} />
          <SentimentCard sentiment={sentiment} />
          <NewsFeed news={news} />
        </div>
        <ExplainabilityPanel explanation={explanation} />
      </main>
      <footer className="dashboard-footer">QuantFormer · Research dashboard <span>Data updates in real time when connected</span></footer>
    </div>
  )
}
