from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import carros


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Container Tracking API", version="0.1.0", lifespan=lifespan)
app.include_router(carros.router)


@app.get("/health")
def health() -> dict[str, str]:
    """Verifica que la API está en línea."""
    return {"status": "ok"}
