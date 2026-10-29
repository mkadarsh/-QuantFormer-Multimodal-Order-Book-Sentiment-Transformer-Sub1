import { useEffect, useRef } from 'react'
import { createChart, LineStyle, type IChartApi, type ISeriesApi, type CandlestickData, type LineData, type Time } from 'lightweight-charts'
import type { PredictionData, PricePoint } from '../types'
import PredictionOverlay from './PredictionOverlay'

interface CandlestickChartProps {
  history: PricePoint[]
  prediction: PredictionData | null
}

function buildCandles(history: PricePoint[]): CandlestickData[] {
  const sorted = [...history].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
  return sorted.map((point, index) => {
    const previous = sorted[index - 1]?.last_price ?? point.last_price
    const open = previous
    const close = point.last_price
    const high = Math.max(open, close, point.ask ?? close)
    const low = Math.min(open, close, point.bid ?? close)
    return {
      time: Math.floor(new Date(point.timestamp).getTime() / 1000) as Time,
      open,
      high,
      low,
      close,
    }
  }).filter((candle, index, candles) => index === 0 || candle.time !== candles[index - 1].time)
}

export default function CandlestickChart({ history, prediction }: CandlestickChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const predictionSeriesRef = useRef<ISeriesApi<'Line'> | null>(null)
  const lowerSeriesRef = useRef<ISeriesApi<'Line'> | null>(null)
  const upperSeriesRef = useRef<ISeriesApi<'Line'> | null>(null)

  useEffect(() => {
    if (!containerRef.current) return
    const chart = createChart(containerRef.current, {
      layout: { background: { color: 'transparent' }, textColor: '#8c98ad' },
      grid: { vertLines: { color: 'rgba(148, 163, 184, 0.08)' }, horzLines: { color: 'rgba(148, 163, 184, 0.08)' } },
      width: containerRef.current.clientWidth,
      height: 330,
      rightPriceScale: { borderColor: 'rgba(148, 163, 184, 0.15)' },
      timeScale: { borderColor: 'rgba(148, 163, 184, 0.15)', timeVisible: true, secondsVisible: false },
    })
    const series = chart.addCandlestickSeries({
      upColor: '#26c281',
      downColor: '#f05d6c',
      borderVisible: false,
      wickUpColor: '#26c281',
      wickDownColor: '#f05d6c',
    })
    const predictionSeries = chart.addLineSeries({ color: '#f7c948', lineWidth: 3, lineStyle: LineStyle.Dashed, title: 'TFT forecast' })
    const lowerSeries = chart.addLineSeries({ color: 'rgba(247, 201, 72, 0.55)', lineWidth: 1, lineStyle: LineStyle.Dotted, title: 'Lower bound' })
    const upperSeries = chart.addLineSeries({ color: 'rgba(247, 201, 72, 0.55)', lineWidth: 1, lineStyle: LineStyle.Dotted, title: 'Upper bound' })
    chartRef.current = chart
    seriesRef.current = series
    predictionSeriesRef.current = predictionSeries
    lowerSeriesRef.current = lowerSeries
    upperSeriesRef.current = upperSeries
    const resizeObserver = new ResizeObserver(() => {
      if (containerRef.current) chart.applyOptions({ width: containerRef.current.clientWidth })
    })
    resizeObserver.observe(containerRef.current)
    return () => {
      resizeObserver.disconnect()
      chart.remove()
      chartRef.current = null
      seriesRef.current = null
      predictionSeriesRef.current = null
      lowerSeriesRef.current = null
      upperSeriesRef.current = null
    }
  }, [])

  useEffect(() => {
    const candles = buildCandles(history)
    if (seriesRef.current && candles.length > 0) {
      seriesRef.current.setData(candles)
      chartRef.current?.timeScale().fitContent()
    }
  }, [history])

  useEffect(() => {
    if (!prediction) {
      predictionSeriesRef.current?.setData([])
      lowerSeriesRef.current?.setData([])
      upperSeriesRef.current?.setData([])
      return
    }
    const start = Math.floor(new Date(prediction.timestamp).getTime() / 1000)
    const end = (start + 300) as Time
    const forecast: LineData[] = [
      { time: start as Time, value: prediction.current_price },
      { time: end, value: prediction.predicted_price },
    ]
    const lower: LineData[] = [
      { time: start as Time, value: prediction.current_price },
      { time: end, value: prediction.lower_bound },
    ]
    const upper: LineData[] = [
      { time: start as Time, value: prediction.current_price },
      { time: end, value: prediction.upper_bound },
    ]
    predictionSeriesRef.current?.setData(forecast)
    lowerSeriesRef.current?.setData(lower)
    upperSeriesRef.current?.setData(upper)
  }, [prediction])

  return (
    <section className="panel chart-panel">
      <div className="card-heading"><div><span className="eyebrow">Price action</span><h2>Live candlestick chart</h2></div><span className="chart-period">1m</span></div>
      <div className="chart-wrap"><div ref={containerRef} className="chart-container" /><PredictionOverlay prediction={prediction} /></div>
      {history.length === 0 && <div className="chart-empty">Waiting for market history…</div>}
    </section>
  )
}
