from fastapi import FastAPI
from .routers import ferries

app = FastAPI()

app.include_router(ferries.router)