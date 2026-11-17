# Coastline frontend

The React app displays upcoming BC Ferries sailings from the data platform API,
with date, route, and text filters.

## Run locally

The frontend reads the live API at
<https://bc-ferry-data-platform.onrender.com>. Start the frontend:

```powershell
npm ci
npm run dev
```

The development server is available at <http://localhost:5173>. Vite proxies
API requests to the hosted backend; a local backend is not required.

Production builds request the hosted API directly. Redeploy the backend with
its CORS configuration before using the deployed frontend in a browser.

## Checks

```powershell
npm run build
npm run lint
```
