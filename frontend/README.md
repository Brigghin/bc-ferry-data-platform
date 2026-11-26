# Coastline frontend

The React app shows BC Ferries sailings from the data platform API.

- Pick an origin and destination terminal; the swap button reverses the trip
  when the reverse route exists.
- Sailings are shown one day at a time. The ‹ and › buttons beside the date
  step through the days the API returns (today, plus any next-day sailings in
  the feed).
- Each row shows the departure (actual, with the scheduled time underneath when
  it differs), the arrival (actual, or an "ETA" of departure plus the route's
  sailing duration when upstream gives none), the ferry, and a fill percentage
  meter.
- Arrived sailings are greyed out: status `arrived`, or `departed` with a
  passed ETA, because upstream never marks Swartz Bay departures as arrived.
- Cancelled sailings have a struck-through time, a red "Cancelled" label, and
  show 0% full.
- If loading takes more than 3 seconds, it shows a "Waking up the server" hint (the
  hosted backend cold-starts when idle).

## Run locally

The frontend reads the live API at
<https://bc-ferry-data-platform.onrender.com>. Start the frontend:

```sh
npm ci
npm run dev
```

The development server is available at <http://localhost:5173>. Vite proxies
`/api` requests to the hosted backend; a local backend is not required.

Production builds request the hosted API directly. The backend allows
cross-origin `GET` requests from any origin.

## Checks

```sh
npm run build
npm run lint
```
