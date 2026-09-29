# BC Ferry Data Platform API

A FastAPI service that retrieves and serves BC Ferries sailing schedules.

## Requirements

- Python 3.14
- [uv](https://docs.astral.sh/uv/)

The `.python-version` file selects Python 3.14 for local development. The `uv.lock` file pins the resolved dependency versions.

## Run locally

From the `backend` directory, install the project dependencies and start the development server:

```powershell
uv sync --locked
uv run fastapi dev
```

The API is available at <http://127.0.0.1:8000>. Interactive API documentation is at <http://127.0.0.1:8000/docs>.

## Endpoint

### `GET /version/`

Returns the installed backend package version.

Example response:

```json
{
	"version": "0.1.0"
}
```

### `GET /ferries/`

Returns ferry routes and their non-capacity sailings. Each route includes its source and destination terminal codes and a list of sailing times.

Example response:

```json
[
	{
		"source": "FROM",
		"destination": "TO",
		"ferries": [
			{
				"departed": false,
				"departure_time": "8:30",
				"arrival_time": "10:05"
			}
		]
	}
]
```

The `departed` value is calculated using the server's current time. Times are returned as strings in 24-hour format.

## Data source

Each request fetches current non-capacity sailing data from the [BC Ferries API](https://www.bcferriesapi.ca/v2/noncapacity/). This service does not currently store or cache the data, so the endpoint depends on the upstream API being available.

