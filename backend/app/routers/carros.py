from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencias import carro_accesible, permisos_de, requiere_permiso, requiere_roles, usuario_actual
from app.models import Carro, EstadoCarro, Rol, TipoCarro, Usuario
from app.schemas import CargaCarro, CarroCreate, CarroOut
from app.services import carros as servicio

# Consultar carros: cualquier usuario con sesión iniciada, pero solo los de su proceso.
# Cada operación que cambia datos exige además un permiso (ver app/permisos.py).
router = APIRouter(prefix="/carros", tags=["carros"], dependencies=[Depends(usuario_actual)])


@router.post(
    "",
    response_model=CarroOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requiere_roles(Rol.ADMIN))],
)
def crear_carro(datos: CarroCreate, db: Session = Depends(get_db)):
    carro = Carro(numero=datos.numero, tipo=datos.tipo)
    db.add(carro)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un carro con ese número")
    return carro


@router.get("", response_model=list[CarroOut])
def listar_carros(
    estado: EstadoCarro | None = None,
    numero: str | None = None,
    tipo: TipoCarro | None = None,
    contenedor_elemento: str | None = None,
    usuario: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
):
    permisos = permisos_de(usuario)
    if tipo is not None and not permisos.ve(tipo):
        return []  # pidió carros de otro proceso: para él no hay ninguno
    return servicio.listar_carros(
        db, estado, numero, permisos.tipo or tipo, contenedor_elemento=contenedor_elemento
    )


@router.get("/{carro_id}", response_model=CarroOut)
def obtener_carro(carro: Carro = Depends(carro_accesible)):
    return carro


@router.post(
    "/{carro_id}/carga",
    response_model=CarroOut,
    dependencies=[Depends(requiere_permiso("cargar")), Depends(carro_accesible)],
)
def cargar_carro(carro_id: int, datos: CargaCarro, db: Session = Depends(get_db)):
    return servicio.cargar_carro(db, carro_id, datos.contenedor_elemento)


@router.post(
    "/{carro_id}/entrega",
    response_model=CarroOut,
    dependencies=[Depends(requiere_permiso("liberar")), Depends(carro_accesible)],
)
def entregar_carro(carro_id: int, db: Session = Depends(get_db)):
    return servicio.entregar_carro(db, carro_id)
