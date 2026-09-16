from pydantic import BaseModel

class ferry_route(BaseModel):
    source: str
    destination: str
    ferries: list[ferries_timing]

class ferries_timing(BaseModel):
    departed: bool
    departure_time: str
    arrival_time: str