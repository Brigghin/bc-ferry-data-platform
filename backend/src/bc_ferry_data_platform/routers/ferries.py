from datetime import time, datetime

import httpx
from fastapi import APIRouter, HTTPException

from ..models.ferries import ferry_route
from ..services.ferries import fetch_ferries

BASE_URL = "https://www.bcferriesapi.ca/v2"

router = APIRouter(prefix="/ferries")
    
'''
Get a list of all ferries and their corresponding departure and arrival times.
'''
@router.get("/", response_model=list[ferry_route])
async def list_ferries() -> list[ferry_route]:
    return await fetch_ferries()
