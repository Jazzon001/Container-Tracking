from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.models import EstadoCarro

# Un solo lugar define cómo se validan los códigos escritos o escaneados:
# se recortan espacios y no pueden quedar vacíos.
Codigo = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]


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
