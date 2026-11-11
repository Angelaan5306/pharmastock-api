from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import init_db
from routes import resource, transaction

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="PharmaStock API",
    description=(
        "REST API backend untuk manajemen obat dan transaksi penjualan apotek. "
        "Dibangun dengan FastAPI, SQLite, aiosqlite, BackgroundTasks, dan asyncio.Lock."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(resource.router)
app.include_router(transaction.router)

@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ok",
        "application": "PharmaStock API",
        "message": "API manajemen apotek siap digunakan",
        "docs": "/docs",
    }