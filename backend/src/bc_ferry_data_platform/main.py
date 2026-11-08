"""Create the FastAPI app and register its routers."""

from fastapi import FastAPI

from .routers import ferries, version

app = FastAPI()

app.include_router(ferries.router)
app.include_router(version.router)
