from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.models import EstadoCarro, Rol

# Un solo lugar define cómo se validan los códigos escritos o escaneados:
# se recortan espacios y no pueden quedar vacíos.
Codigo = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]

# Las contraseñas no se recortan: los espacios pueden ser parte de ellas.
Password = Annotated[str, StringConstraints(min_length=8, max_length=128)]


class CarroCreate(BaseModel):
    numero: Codigo


class CargaCarro(BaseModel):
    contenedor_elemento: Codigo


class CarroOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: str
    estado: EstadoCarro
    contenedor_elemento: str | None


class MantenimientoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    carro_id: int
    fecha_entrada: datetime
    fecha_salida: datetime | None


class LoginIn(BaseModel):
    username: Codigo
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UsuarioCreate(BaseModel):
    username: Codigo
    password: Password
    rol: Rol


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    rol: Rol
