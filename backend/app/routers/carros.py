from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Carro
from app.schemas import CarroCreate, CarroOut

router = APIRouter(prefix="/carros", tags=["carros"])


@router.post("", response_model=CarroOut, status_code=status.HTTP_201_CREATED)
def crear_carro(datos: CarroCreate, db: Session = Depends(get_db)):
    numero = datos.numero.strip()
    if not numero:
        raise HTTPException(422,"El número no puede estar vacío")
    carro = Carro(numero=numero)
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
    carro = db.get(Carro, carro_id)
    if carro is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Carro no encontrado")
    return carro
