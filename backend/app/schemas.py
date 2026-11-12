from datetime import datetime, timezone
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, StringConstraints

from app.models import EstadoCarro, Rol, TipoCarro


def _como_utc(fecha: datetime) -> datetime:
    """Todas las fechas se guardan en UTC, pero SQLite las devuelve sin zona horaria.
    Se les agrega, para que el frontend no las confunda con la hora local."""
    return fecha.replace(tzinfo=timezone.utc) if fecha.tzinfo is None else fecha


FechaUTC = Annotated[datetime, AfterValidator(_como_utc)]

# Un solo lugar define cómo se validan los códigos escritos o escaneados:
# se recortan espacios y no pueden quedar vacíos.
Codigo = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]

# Las contraseñas no se recortan: los espacios pueden ser parte de ellas.
Password = Annotated[str, StringConstraints(min_length=8, max_length=128)]


class CarroCreate(BaseModel):
    numero: Codigo
    tipo: TipoCarro


class CargaCarro(BaseModel):
    contenedor_elemento: Codigo


class CarroOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: str
    tipo: TipoCarro
    estado: EstadoCarro
    contenedor_elemento: str | None
    estado_desde: FechaUTC


class MantenimientoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    carro_id: int
    fecha_entrada: FechaUTC
    fecha_salida: FechaUTC | None


class LoginIn(BaseModel):
    username: Codigo
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    # El frontend lo usa solo para mostrar u ocultar opciones; la API sigue
    # validando el permiso en cada petición.
    rol: Rol


class UsuarioCreate(BaseModel):
    username: Codigo
    password: Password
    rol: Rol


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    rol: Rol
