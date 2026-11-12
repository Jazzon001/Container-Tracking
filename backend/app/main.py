import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.errores import ErrorDeNegocio
from app.migraciones import aplicar_migraciones
from app.routers import auth, carros, mantenimiento, usuarios


@asynccontextmanager
async def lifespan(app: FastAPI):
    aplicar_migraciones()
    yield


app = FastAPI(title="Container Tracking API", version="0.1.0", lifespan=lifespan)

# Orígenes (dominios) del frontend que pueden llamar a la API desde el navegador.
# En producción se define CORS_ORIGINS con el dominio de Vercel, separado por comas.
ORIGENES_PERMITIDOS = [
    origen.strip()
    for origen in os.environ.get(
        "CORS_ORIGINS", "http://localhost:4200,http://127.0.0.1:4200"
    ).split(",")
    if origen.strip()
]
# Con más de mil carros, la lista pesa cientos de KB y se consulta cada 30 segundos desde
# el celular: comprimirla la reduce a una fracción.
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENES_PERMITIDOS,
    allow_methods=["*"],
    allow_headers=["*"],
)
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
