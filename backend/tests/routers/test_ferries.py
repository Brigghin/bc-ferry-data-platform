"""Tests for the ferry HTTP endpoints."""

from datetime import date, datetime, timezone

from fastapi.testclient import TestClient

from bc_ferry_data_platform.config.settings import settings
from bc_ferry_data_platform.database.dependencies import get_session
from bc_ferry_data_platform.main import app
from bc_ferry_data_platform.schemas.ferries import Route, Sailing

client = TestClient(app)


def sample_route(route_code: str = "TSASWB") -> Route:
    """Build a sample route response."""
    return Route(
        routeCode=route_code,
        fromTerminalCode="TSA",
        toTerminalCode="SWB",
        sailingDuration="1h 35m",
        sailings=[
            Sailing(
                serviceDate=date(2026, 11, 10),
                scheduledTime=datetime(
                    2026, 11, 10, 8, 30, tzinfo=timezone.utc
                ),
                capacityKnown=False,
                carCapacityKnown=False,
                oversizeCapacityKnown=True,
                fill=91,
                carFill=82,
                oversizeFill=13,
                vesselName="Coastal Example",
                status="boarding",
            )
        ],
    )


def test_list_ferries_returns_schema_and_filters_by_route(monkeypatch) -> None:
    """Return routes from storage and pass along route filters."""
    def fetch(_session, route_code):
        normalized_code = (
            route_code.replace("-", "").strip().upper()
            if route_code is not None
            else None
        )
        return [sample_route()] if normalized_code in (None, "TSASWB") else []

    monkeypatch.setitem(app.dependency_overrides, get_session, lambda: None)
    monkeypatch.setattr(
        "bc_ferry_data_platform.routers.ferries.fetch_storage_ferries",
        fetch,
    )

    response = client.get("/ferries/")

    assert response.status_code == 200
    assert response.json()[0]["routeCode"] == "TSASWB"
    assert response.json()[0]["sailings"][0]["vesselName"] == "Coastal Example"

    filtered_response = client.get("/ferries/?route_code=TSA-SWB")

    assert filtered_response.status_code == 200
    assert len(filtered_response.json()) == 1

    missing_response = client.get("/ferries/?route_code=HSB-NAN")

    assert missing_response.status_code == 200
    assert missing_response.json() == []


def test_refresh_endpoint_returns_processed_route_count(monkeypatch) -> None:
    """Expose the number of refreshed routes as the endpoint response."""
    monkeypatch.setitem(app.dependency_overrides, get_session, lambda: None)
    monkeypatch.setattr(
        "bc_ferry_data_platform.routers.ferries.upload_ferries", lambda _session: 2
    )
    monkeypatch.setattr(settings, "refresh_token", "secret")

    response = client.post("/ferries/refresh", headers={"X-Refresh-Token": "secret"})

    assert response.status_code == 200
    assert response.json() == 2


def test_refresh_endpoint_rejects_missing_or_wrong_token(monkeypatch) -> None:
    """Only callers with the configured token may trigger a refresh."""
    monkeypatch.setitem(app.dependency_overrides, get_session, lambda: None)
    monkeypatch.setattr(
        "bc_ferry_data_platform.routers.ferries.upload_ferries", lambda _session: 2
    )

    monkeypatch.setattr(settings, "refresh_token", "")
    assert client.post("/ferries/refresh").status_code == 401

    monkeypatch.setattr(settings, "refresh_token", "secret")
    assert client.post("/ferries/refresh").status_code == 401
    assert client.post(
        "/ferries/refresh", headers={"X-Refresh-Token": "wrong"}
    ).status_code == 401


def test_api_allows_cross_origin_reads() -> None:
    """Allow browser frontends on another origin to read the public API."""
    response = client.get(
        "/version/",
        headers={"Origin": "https://coastline.example"},
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
