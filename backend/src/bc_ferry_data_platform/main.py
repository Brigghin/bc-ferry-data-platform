from fastapi import FastAPI
from .routers import ferries
from .routers import version

app = FastAPI()

app.include_router(ferries.router)
app.include_router(version.router)