from fastapi import FastAPI

app = FastAPI(title="Container Tracking API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Verifica que la API está en línea."""
    return {"status": "ok"}
