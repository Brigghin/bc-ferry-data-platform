import { useEffect, useState } from 'react'
import {
  Anchor,
  ArrowRight,
  CircleAlert,
  Clock3,
  RefreshCw,
  Ship,
  Waves,
} from 'lucide-react'
import './App.css'

type SailingStatus = 'future' | 'current' | 'past' | 'unknown'

interface Sailing {
  departureTime: string
  arrivalTime: string
  status: SailingStatus
  vessel: string
  fill: number
  carFill: number
  oversizeFill: number
  sailingDate: string
  capturedAt: string | null
}

interface FerryRoute {
  routeCode: string
  source: string
  destination: string
  duration: string
  ferries: Sailing[]
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')

async function fetchRoutes(signal?: AbortSignal): Promise<FerryRoute[]> {
  const response = await fetch(`${API_BASE_URL}/ferries/`, { signal })
  if (!response.ok) {
    throw new Error(`Could not load schedules (${response.status}).`)
  }
  return response.json() as Promise<FerryRoute[]>
}

function formatTime(value: string): string {
  if (!value) return 'Not posted'
  const [hoursPart, minutesPart] = value.split(':')
  const hours = Number(hoursPart)
  const minutes = Number(minutesPart)
  if (!Number.isFinite(hours) || !Number.isFinite(minutes)) return value || '—'
  const suffix = hours >= 12 ? 'PM' : 'AM'
  const displayHour = hours % 12 || 12
  return `${displayHour}:${String(minutes).padStart(2, '0')} ${suffix}`
}

function estimateArrivalTime(departureTime: string, duration: string): string | null {
  const departureMatch = /^(\d{1,2}):(\d{2})$/.exec(departureTime)
  const durationMatch = /^(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?$/i.exec(duration.trim())
  if (!departureMatch || !durationMatch || (!durationMatch[1] && !durationMatch[2])) {
    return null
  }

  const departureHours = Number(departureMatch[1])
  const departureMinutes = Number(departureMatch[2])
  const durationHours = Number(durationMatch[1] ?? 0)
  const durationMinutes = Number(durationMatch[2] ?? 0)
  if (
    departureHours > 23 ||
    departureMinutes > 59 ||
    durationHours + durationMinutes <= 0
  ) {
    return null
  }

  const totalMinutes = departureHours * 60 + departureMinutes + durationHours * 60 + durationMinutes
  const dayOffset = Math.floor(totalMinutes / (24 * 60))
  const arrivalMinutes = totalMinutes % (24 * 60)
  const arrivalTime = `${Math.floor(arrivalMinutes / 60)}:${String(arrivalMinutes % 60).padStart(2, '0')}`
  const daySuffix = dayOffset > 0 ? ` (+${dayOffset}d)` : ''

  return `${formatTime(arrivalTime)}${daySuffix}`
}

function formatSailingDate(value: string): string {
  if (!value) return '—'
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'UTC',
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  }).format(new Date(`${value}T12:00:00Z`))
}

function formatCapturedAt(value: number | null): string {
  if (value === null) return 'Not recorded'
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Vancouver',
    hour: 'numeric',
    minute: '2-digit',
    }).format(new Date(value))
}

function App() {
  const [routes, setRoutes] = useState<FerryRoute[]>([])
  const [baseTerminal, setBaseTerminal] = useState('')
  const [destinationTerminal, setDestinationTerminal] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [notice, setNotice] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    fetchRoutes(controller.signal)
      .then(setRoutes)
      .catch((error: unknown) => {
        if (error instanceof Error && error.name === 'AbortError') return
        setErrorMessage(
          error instanceof Error ? error.message : 'Unable to load ferry schedules.',
        )
      })
      .finally(() => setIsLoading(false))

    return () => controller.abort()
  }, [])

  const latestCapture = routes
    .flatMap((route) => route.ferries)
    .map((sailing) => sailing.capturedAt)
    .filter((value): value is string => value !== null)
    .map((value) => Date.parse(value))
    .filter(Number.isFinite)
    .reduce<number | null>(
      (latest, value) => (latest === null ? value : Math.max(latest, value)),
      null,
    )

  const baseTerminals = [...new Set(routes.map((route) => route.source))].sort()
  const destinationTerminals = [...new Set(routes.map((route) => route.destination))].sort()

  const visibleDepartures = routes
    .filter((route) => !baseTerminal || route.source === baseTerminal)
    .filter((route) => !destinationTerminal || route.destination === destinationTerminal)
    .flatMap((route) =>
      route.ferries
        .filter((sailing) => {
          return (
            latestCapture !== null &&
            sailing.capturedAt !== null &&
            Date.parse(sailing.capturedAt) === latestCapture
          )
        })
        .map((sailing) => ({ route, sailing })),
    )
    .sort((left, right) => {
      const dateOrder = left.sailing.sailingDate.localeCompare(right.sailing.sailingDate)
      if (dateOrder !== 0) return dateOrder

      const toMinutes = (time: string) => {
        const [hours = '0', minutes = '0'] = time.split(':')
        return Number(hours) * 60 + Number(minutes)
      }
      return toMinutes(left.sailing.departureTime) - toMinutes(right.sailing.departureTime)
    })

  const visibleRouteCount = new Set(
    visibleDepartures.map(({ route }) => route.routeCode),
  ).size
  const nextSailing = visibleDepartures.find(({ sailing }) => sailing.status === 'future')
  async function handleRefresh() {
    setIsRefreshing(true)
    setErrorMessage('')
    setNotice('')

    try {
      const response = await fetch(`${API_BASE_URL}/ferries/refresh`, { method: 'POST' })
      if (!response.ok) {
        throw new Error(`Refresh failed (${response.status}).`)
      }
      const updatedRoutes = (await response.json()) as number
      setRoutes(await fetchRoutes())
      setNotice(`Refresh complete. ${updatedRoutes} routes checked.`)
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to refresh schedules.')
    } finally {
      setIsRefreshing(false)
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="wordmark" href="#top" aria-label="Coastline schedules home">
          <span className="wordmark-mark"><Anchor size={18} strokeWidth={2.2} /></span>
          <span>COASTLINE<span className="wordmark-light"> / SCHEDULES</span></span>
        </a>
        <div className="topbar-meta">
          <span className="live-dot" />
          <span>BRITISH COLUMBIA</span>
        </div>
      </header>

      <main id="top" className="main-content">
        <section className="heading-row" aria-labelledby="page-title">
          <div>
            <p className="eyebrow"><Waves size={14} /> BC FERRIES / LIVE BOARD</p>
            <h1 id="page-title">Sailing schedule</h1>
            <p className="page-subtitle">Routes and departures across the coast.</p>
          </div>
          <button
            className="refresh-button"
            type="button"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw size={16} className={isRefreshing ? 'spin' : undefined} />
            {isRefreshing ? 'Refreshing' : 'Refresh data'}
          </button>
        </section>

        <section className="summary-row" aria-label="Schedule summary">
          <div className="summary-item">
            <span className="summary-label">SAILINGS SHOWN</span>
            <strong>{isLoading ? '—' : visibleDepartures.length}</strong>
          </div>
          <div className="summary-item">
            <span className="summary-label">ROUTES SERVED</span>
            <strong>{isLoading ? '—' : visibleRouteCount}</strong>
          </div>
          <div className="summary-item summary-next">
            <span className="summary-label">NEXT DEPARTURE</span>
            <strong>
              {nextSailing ? formatTime(nextSailing.sailing.departureTime) : '—'}
            </strong>
            {nextSailing && (
              <span className="summary-detail">
                {nextSailing.route.source} <ArrowRight size={12} /> {nextSailing.route.destination}
              </span>
            )}
          </div>
          <div className="summary-item summary-updated">
            <span className="summary-label">LAST CAPTURED</span>
            <strong>{formatCapturedAt(latestCapture ?? null)}</strong>
            <span className="summary-detail">Pacific time</span>
          </div>
        </section>

        <section className="schedule-section" aria-labelledby="schedule-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">DEPARTURE BOARD</p>
              <h2 id="schedule-title">Latest refresh</h2>
            </div>
            <p className="capture-label">Captured {formatCapturedAt(latestCapture)} Pacific time</p>
          </div>

          <div className="terminal-filters">
            <label className="terminal-control">
              <span>BASE TERMINAL</span>
              <select value={baseTerminal} onChange={(event) => setBaseTerminal(event.target.value)}>
                <option value="">All bases</option>
                {baseTerminals.map((terminal) => <option key={terminal} value={terminal}>{terminal}</option>)}
              </select>
            </label>
            <label className="terminal-control">
              <span>DESTINATION TERMINAL</span>
              <select value={destinationTerminal} onChange={(event) => setDestinationTerminal(event.target.value)}>
                <option value="">All destinations</option>
                {destinationTerminals.map((terminal) => <option key={terminal} value={terminal}>{terminal}</option>)}
              </select>
            </label>
          </div>

          {errorMessage && (
            <div className="message message-error" role="alert">
              <CircleAlert size={18} />
              <span>{errorMessage} Check that the backend is running.</span>
            </div>
          )}
          {notice && <p className="message message-success" role="status">{notice}</p>}

          <div className="table-wrap">
            <table className="sailing-table">
              <thead>
                <tr>
                  <th scope="col">ROUTE</th>
                  <th scope="col">SAILING DATE</th>
                  <th scope="col">DEPARTS</th>
                  <th scope="col">ARRIVES</th>
                  <th scope="col">VESSEL</th>
                  <th scope="col">CAR FILL</th>
                  <th scope="col">STATUS</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr><td className="table-message" colSpan={7}>Loading saved schedules…</td></tr>
                ) : visibleDepartures.length === 0 ? (
                  <tr>
                    <td className="table-message" colSpan={7}>
                      <Ship size={22} />
                      <strong>{routes.length === 0 ? 'No saved schedules yet' : 'No sailings in the latest refresh'}</strong>
                      <span>{routes.length === 0 ? 'Refresh data to load sailings from BC Ferries.' : 'Try another base or destination terminal.'}</span>
                    </td>
                  </tr>
                ) : (
                  visibleDepartures.map(({ route, sailing }, index) => {
                    const estimatedArrival = sailing.arrivalTime
                      ? null
                      : estimateArrivalTime(sailing.departureTime, route.duration)

                    return (
                      <tr key={`${route.routeCode}-${sailing.sailingDate}-${sailing.departureTime}-${sailing.vessel}-${sailing.capturedAt}-${index}`}>
                        <td>
                          <div className="route-cell">
                            <span className="route-code">{route.routeCode}</span>
                            <span className="route-terminals">
                              {route.source}<ArrowRight size={12} />{route.destination}
                            </span>
                          </div>
                        </td>
                        <td className="date-cell">{formatSailingDate(sailing.sailingDate)}</td>
                        <td className="time-cell">{formatTime(sailing.departureTime)}</td>
                        <td
                          className={estimatedArrival ? 'arrival-cell arrival-estimate' : 'time-cell arrival-cell'}
                          title={estimatedArrival
                            ? 'Estimated from the scheduled departure and route duration; not an arrival time posted by BC Ferries.'
                            : sailing.arrivalTime
                              ? undefined
                              : 'BC Ferries has not posted an arrival time, and this route has no usable duration.'}
                        >
                          {sailing.arrivalTime
                            ? formatTime(sailing.arrivalTime)
                            : estimatedArrival
                              ? `Est. ${estimatedArrival}`
                              : 'Not posted'}
                        </td>
                        <td className="vessel-cell">{sailing.vessel || '—'}</td>
                        <td>
                          <div className="capacity-cell">
                            <div className="capacity-track" aria-hidden="true">
                              <span style={{ width: `${Math.min(100, Math.max(0, sailing.carFill))}%` }} />
                            </div>
                            <span>{sailing.carFill}%</span>
                          </div>
                        </td>
                        <td>
                          <span className={`status-pill status-${sailing.status}`}>
                            <span className="status-dot" />
                            {sailing.status}
                          </span>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>

          <footer className="board-footer">
            <span><Clock3 size={14} /> Times shown in Pacific time</span>
            <span>{visibleDepartures.length} {visibleDepartures.length === 1 ? 'departure' : 'departures'}</span>
          </footer>
        </section>
      </main>
    </div>
  )
}

export default App
