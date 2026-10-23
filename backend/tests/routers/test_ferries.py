'''Test files for the routers/ferries file'''
from fastapi.testclient import TestClient
from bc_ferry_data_platform.main import app
from bc_ferry_data_platform.database.dependencies import get_session
from bc_ferry_data_platform.schemas.ferries import FerryRoute

client = TestClient(app)

def test_fetch_ferries(monkeypatch):
    '''Test the fetch_ferries function'''
    def mock_fetch_storage_ferries(_session, route_code):
        assert _session is None
        ferries = [
            {
                "routeCode": "TSASWB",
                "source": "TSA",
                "destination": "SWB",
                "duration": "1h 35m",
                "ferries": []
            },
            {
                "routeCode": "HSBNAN",
                "source": "HSB",
                "destination": "NAN",
                "duration": "1h 35m",
                "ferries": []
            }
        ]
        if route_code is None:
            selected = ferries
        else:
            selected = [
                route for route in ferries
                if route["routeCode"] == route_code
            ]

        return [FerryRoute.model_validate(route) for route in selected]

    def override_get_session():
        return None

    monkeypatch.setitem(app.dependency_overrides, get_session, override_get_session)

    monkeypatch.setattr(
        "bc_ferry_data_platform.routers.ferries.fetch_storage_ferries",
        mock_fetch_storage_ferries
    )

    #Testing getting all entries
    response = client.get("/ferries")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["routeCode"] == "TSASWB"
    assert data[1]["routeCode"] == "HSBNAN"

    #Testing filtering
    response = client.get("/ferries?route_code=TSASWB")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["routeCode"] == "TSASWB"
    assert data[0]["source"] == "TSA"
    assert data[0]["destination"] == "SWB"

    #Testing filtering
    response = client.get("/ferries?route_code=HSBNAN")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["routeCode"] == "HSBNAN"
    assert data[0]["source"] == "HSB"
    assert data[0]["destination"] == "NAN"

    #Testing filtering with non existant entry
    response = client.get("/ferries?route_code=HSBBOW")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0
