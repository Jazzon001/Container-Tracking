import enum

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EstadoCarro(str, enum.Enum):
    DISPONIBLE = "disponible"
    EN_TRANSITO = "en_transito"
    EN_MANTENIMIENTO = "en_mantenimiento"


class Carro(Base):
    """Carro (contenedor de 24 bobinas) que circula entre procesos."""

    __tablename__ = "carros"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    estado: Mapped[EstadoCarro] = mapped_column(
        Enum(EstadoCarro), default=EstadoCarro.DISPONIBLE
    )
    # Código de NOW del producto que lleva el carro. Es nulo si el carro va vacío.
    # Único: un mismo contenedor elemento no puede estar en dos carros a la vez.
    contenedor_elemento: Mapped[str | None] = mapped_column(
        String(50), unique=True, default=None
    )
