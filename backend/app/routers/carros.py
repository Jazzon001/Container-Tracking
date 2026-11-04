from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Carro
from app.schemas import CargaCarro, CarroCreate, CarroOut
from app.services import carros as servicio

router = APIRouter(prefix="/carros", tags=["carros"])


@router.post("", response_model=CarroOut, status_code=status.HTTP_201_CREATED)
def crear_carro(datos: CarroCreate, db: Session = Depends(get_db)):
    carro = Carro(numero=datos.numero)
    db.add(carro)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un carro con ese número")
    return carro


@router.get("", response_model=list[CarroOut])
def listar_carros(db: Session = Depends(get_db)):
    return db.scalars(select(Carro).order_by(Carro.id)).all()


@router.get("/{carro_id}", response_model=CarroOut)
def obtener_carro(carro_id: int, db: Session = Depends(get_db)):
    return servicio.obtener_carro(db, carro_id)


@router.post("/{carro_id}/carga", response_model=CarroOut)
def cargar_carro(carro_id: int, datos: CargaCarro, db: Session = Depends(get_db)):
    return servicio.cargar_carro(db, carro_id, datos.contenedor_elemento)
