"""Create the FastAPI app and register its routers."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import ferries, version

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
)

app.include_router(ferries.router)
app.include_router(version.router)
