from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import Base, engine
from app.routers import carros
from app.services.carros import (
    CarroNoEncontrado,
    ContenedorEnUso,
    ErrorDeNegocio,
    EstadoInvalido,
)

# Código HTTP de cada error de negocio. Es el único lugar que los relaciona.
CODIGOS_HTTP = {CarroNoEncontrado: 404, EstadoInvalido: 409, ContenedorEnUso: 409}


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Container Tracking API", version="0.1.0", lifespan=lifespan)
app.include_router(carros.router)


@app.exception_handler(ErrorDeNegocio)
async def manejar_error_de_negocio(request: Request, error: ErrorDeNegocio):
    return JSONResponse(status_code=CODIGOS_HTTP[type(error)], content={"detail": str(error)})


@app.get("/health")
def health() -> dict[str, str]:
    """Verifica que la API está en línea."""
    return {"status": "ok"}
