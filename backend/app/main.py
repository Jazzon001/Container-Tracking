from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import Base, engine
from app.errores import ErrorDeNegocio
from app.routers import auth, carros, mantenimiento, usuarios


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Container Tracking API", version="0.1.0", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(carros.router)
app.include_router(mantenimiento.router)


@app.exception_handler(ErrorDeNegocio)
async def manejar_error_de_negocio(request: Request, error: ErrorDeNegocio):
    return JSONResponse(status_code=error.codigo_http, content={"detail": str(error)})


@app.get("/health")
def health() -> dict[str, str]:
    """Verifica que la API está en línea."""
    return {"status": "ok"}
