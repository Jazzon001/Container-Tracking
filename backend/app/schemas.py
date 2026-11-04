from pydantic import BaseModel, ConfigDict, Field

from app.models import EstadoCarro


class CarroCreate(BaseModel):
    numero: str = Field(min_length=1, max_length=50)


class CarroOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: str
    estado: EstadoCarro
