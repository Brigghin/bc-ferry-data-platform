'''Test files for the routers/ferries file'''
from fastapi.testclient import TestClient
from bc_ferry_data_platform.main import app

client = TestClient(app)

def test_fetch_ferries(monkeypatch):
    '''Test the fetch_ferries function'''
    async def mock_fetch_ferries(route_code):
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
            return ferries

        return [
            route for route in ferries
            if route["routeCode"] == route_code
        ]


    monkeypatch.setattr(
        "bc_ferry_data_platform.routers.ferries.fetch_ferries",
        mock_fetch_ferries
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
