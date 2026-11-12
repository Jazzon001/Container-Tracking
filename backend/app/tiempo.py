from datetime import datetime, timezone


def ahora() -> datetime:
    """Instante actual en UTC. Todas las fechas del sistema se guardan en UTC."""
    return datetime.now(timezone.utc)
