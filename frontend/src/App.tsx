import { useEffect, useMemo, useState } from 'react'
import './App.css'

type Sailing = {
  serviceDate: string
  scheduledTime: string | null
  actualDepartureTime: string | null
  actualArrivalTime: string | null
  capacityKnown: boolean
  carCapacityKnown: boolean
  oversizeCapacityKnown: boolean
  fill: number
  carFill: number
  oversizeFill: number
  vesselName: string
  status: string
  observedAt: string | null
  APICapturedAt: string | null
}

type FerryRoute = {
  routeCode: string
  fromTerminalCode: string
  toTerminalCode: string
  sailingDuration: string
  sailings: Sailing[]
}

const timeZone = 'America/Vancouver'
const apiBaseUrl = import.meta.env.DEV
  ? '/api'
  : 'https://bc-ferry-data-platform.onrender.com'

const terminalNames: Record<string, string> = {
  TSA: 'Tsawwassen (Vancouver)',
  SWB: 'Swartz Bay (Victoria)',
  HSB: 'Horseshoe Bay (West Vancouver)',
  DUK: 'Duke Point (Nanaimo)',
  NAN: 'Departure Bay (Nanaimo)',
  LNG: 'Langdale (Sunshine Coast)',
  BOW: 'Snug Cove (Bowen Island)',
}

function terminalName(code: string): string {
  return terminalNames[code] ?? code
}

function getTodayInBCTime(): string {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(new Date())
  const part = (type: string) => parts.find((item) => item.type === type)?.value ?? ''
  return `${part('year')}-${part('month')}-${part('day')}`
}

function formatTime(value: string | null): string {
  if (!value) return '—'
  return new Intl.DateTimeFormat('en-CA', {
    timeZone,
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value))
}

function App() {
  const [routes, setRoutes] = useState<FerryRoute[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [origin, setOrigin] = useState('')
  const [destination, setDestination] = useState('')
  const [reloadCount, setReloadCount] = useState(0)

  useEffect(() => {
    const controller = new AbortController()

    async function loadSchedule() {
      setLoading(true)
      setError('')
      try {
        const response = await fetch(`${apiBaseUrl}/ferries/`, {
          signal: controller.signal,
        })
        if (!response.ok) {
          throw new Error(`Schedule request failed (${response.status}).`)
        }
        const data: FerryRoute[] = await response.json()
        setRoutes(data)
      } catch (reason) {
        if (reason instanceof Error && reason.name === 'AbortError') return
        setError(
          reason instanceof Error
            ? reason.message
            : 'The sailing schedule could not be loaded.',
        )
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    }

    void loadSchedule()
    return () => controller.abort()
  }, [reloadCount])

  const origins = useMemo(
    () =>
      [...new Set(routes.map((route) => route.fromTerminalCode))].sort((a, b) =>
        terminalName(a).localeCompare(terminalName(b)),
      ),
    [routes],
  )

  const destinations = useMemo(
    () =>
      routes
        .filter((route) => route.fromTerminalCode === origin)
        .map((route) => route.toTerminalCode)
        .sort((a, b) => terminalName(a).localeCompare(terminalName(b))),
    [routes, origin],
  )

  const findRoute = (from: string, to: string) =>
    routes.find(
      (route) => route.fromTerminalCode === from && route.toTerminalCode === to,
    )

  const selectedRoute = origin && destination ? findRoute(origin, destination) : undefined
  const canSwap = Boolean(selectedRoute && findRoute(destination, origin))

  const sailings = useMemo(() => {
    if (!selectedRoute) return []
    const today = getTodayInBCTime()
    return selectedRoute.sailings
      .filter((sailing) => sailing.serviceDate === today)
      .sort((a, b) => {
        if (!a.scheduledTime) return 1
        if (!b.scheduledTime) return -1
        return a.scheduledTime.localeCompare(b.scheduledTime)
      })
  }, [selectedRoute])

  function chooseOrigin(code: string) {
    setOrigin(code)
    if (!findRoute(code, destination)) setDestination('')
  }

  function swap() {
    setOrigin(destination)
    setDestination(origin)
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Coastline home">
          <svg className="brand-mark" viewBox="0 0 32 32" fill="none" aria-hidden="true">
            <path d="M4 20.5c4.2 0 4.2-3 8.4-3s4.2 3 8.4 3 4.2-3 7.2-3" />
            <path d="M4 25.5c4.2 0 4.2-3 8.4-3s4.2 3 8.4 3 4.2-3 7.2-3" />
            <path d="M10 14h13l-2-5H13l-3 5Zm4 0v-5m5 5v-5" />
          </svg>
          <span className="brand-name">coastline<span>.</span></span>
        </a>
      </header>

      <main className="main-content">
        <h1>Where are you sailing?</h1>

        <div className="selectors">
          <label className="field">
            <span className="field-label">From</span>
            <span className="select-wrap">
              <select
                value={origin}
                onChange={(event) => chooseOrigin(event.target.value)}
                disabled={loading || Boolean(error)}
              >
                <option value="">{loading ? 'Loading…' : 'Choose origin'}</option>
                {origins.map((code) => (
                  <option key={code} value={code}>
                    {terminalName(code)}
                  </option>
                ))}
              </select>
              <Chevron />
            </span>
          </label>

          <button
            className="swap-button"
            type="button"
            onClick={swap}
            disabled={!canSwap}
            aria-label="Swap origin and destination"
          >
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M4 8h15m0 0-4-4m4 4-4 4M20 16H5m0 0 4-4m-4 4 4 4" />
            </svg>
          </button>

          <label className="field">
            <span className="field-label">To</span>
            <span className="select-wrap">
              <select
                value={destination}
                onChange={(event) => setDestination(event.target.value)}
                disabled={!origin}
              >
                <option value="">Choose destination</option>
                {destinations.map((code) => (
                  <option key={code} value={code}>
                    {terminalName(code)}
                  </option>
                ))}
              </select>
              <Chevron />
            </span>
          </label>
        </div>

        {error ? (
          <div className="message" role="alert">
            <p>We couldn’t load the sailing schedule. {error}</p>
            <button
              className="text-button"
              type="button"
              onClick={() => setReloadCount((count) => count + 1)}
            >
              Try again
            </button>
          </div>
        ) : selectedRoute ? (
          <section className="sailings" aria-label="Today's sailings" aria-live="polite">
            <div className="sailings-header">
              <span>Today · {selectedRoute.sailingDuration} crossing</span>
              <span>Pacific time</span>
            </div>
            {sailings.length > 0 ? (
              sailings.map((sailing, index) => (
                <SailingRow key={sailing.scheduledTime ?? index} sailing={sailing} />
              ))
            ) : (
              <p className="message">No sailings today on this route.</p>
            )}
          </section>
        ) : (
          !loading && <p className="hint">Pick both ends of your trip to see today’s sailings.</p>
        )}
      </main>
    </div>
  )
}

function SailingRow({ sailing }: { sailing: Sailing }) {
  const fill = Math.min(Math.max(sailing.fill, 0), 100)
  const full = sailing.capacityKnown && fill >= 100
  const level = full ? 'full' : fill >= 80 ? 'busy' : 'open'

  return (
    <div className={`sailing-row${full ? ' is-full' : ''}`}>
      <span className="sailing-time">{formatTime(sailing.scheduledTime)}</span>
      {sailing.capacityKnown ? (
        <span className="sailing-capacity">
          <span className="capacity-label">{full ? 'Full' : `${100 - fill}% space`}</span>
          <span className="capacity-meter">
            <span className={`capacity-${level}`} style={{ width: `${fill}%` }} />
          </span>
        </span>
      ) : (
        <span className="capacity-label">Capacity unavailable</span>
      )}
    </div>
  )
}

function Chevron() {
  return (
    <svg className="select-chevron" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="m4 6 4 4 4-4" />
    </svg>
  )
}

export default App
