import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.tiempo import ahora


class EstadoCarro(str, enum.Enum):
    DISPONIBLE = "disponible"
    EN_TRANSITO = "en_transito"
    EN_MANTENIMIENTO = "en_mantenimiento"


class TipoCarro(str, enum.Enum):
    """Proceso al que pertenece el carro. En NOW es el tipo de producto (C01, C02, C03)."""

    POY = "poy"
    DTY = "dty"
    TWISTING = "twisting"


class Rol(str, enum.Enum):
    POY = "poy"
    ALMACEN = "almacen"
    DTY = "dty"
    TWISTING = "twisting"
    ADMIN = "admin"


class Carro(Base):
    """Carro (contenedor de 24 bobinas) que circula entre procesos."""

    __tablename__ = "carros"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    tipo: Mapped[TipoCarro] = mapped_column(Enum(TipoCarro), index=True)
    estado: Mapped[EstadoCarro] = mapped_column(
        Enum(EstadoCarro), default=EstadoCarro.DISPONIBLE
    )
    # Código de NOW del producto que lleva el carro. Es nulo si el carro va vacío.
    # Único: un mismo contenedor elemento no puede estar en dos carros a la vez.
    contenedor_elemento: Mapped[str | None] = mapped_column(
        String(50), unique=True, default=None
    )
    # Cuándo pasó el carro a su estado actual. Con esto se sabe desde hace cuánto
    # un carro está en tránsito, que es lo que busca el cliente.
    estado_desde: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)


class Mantenimiento(Base):
    """Paso de un carro por mantenimiento. Mientras no tiene salida, sigue abierto."""

    __tablename__ = "mantenimientos"

    id: Mapped[int] = mapped_column(primary_key=True)
    carro_id: Mapped[int] = mapped_column(ForeignKey("carros.id"), index=True)
    fecha_entrada: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fecha_salida: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )


class Usuario(Base):
    """Persona que usa el sistema. Su rol define qué operaciones puede hacer."""

    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    # Nunca se guarda la contraseña, solo su hash con sal.
    password_hash: Mapped[str] = mapped_column(String(200))
    rol: Mapped[Rol] = mapped_column(Enum(Rol))
