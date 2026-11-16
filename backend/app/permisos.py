"""Qué puede hacer cada perfil, en un solo lugar.

Cada perfil tiene un alcance (de qué carros) y tres permisos:
  - cargar:  sacar un carro del stock disponible (lo pone en tránsito);
  - liberar: devolver un carro en tránsito al stock disponible;
  - mantener: registrar la entrada y la salida de mantenimiento;
  - reportes: subir el Excel de NOW y ver el reporte de tiempos (solo el administrador).

Consultar carros y el historial lo puede hacer cualquier perfil, pero solo de los carros de
su alcance: un perfil de POY no ve carros de DTY ni de Twisting.

El frontend tiene la misma tabla (`perfiles.ts`) solo para mostrar u ocultar opciones; esta es
la que manda, porque la API la valida en cada petición.
"""
from dataclasses import dataclass

from app.models import Rol, TipoCarro


@dataclass(frozen=True)
class Permisos:
    tipo: TipoCarro | None  # None: todos los carros
    cargar: bool
    liberar: bool
    mantener: bool
    reportes: bool = False  # subir el Excel de NOW y ver el reporte de tiempos

    def ve(self, tipo: TipoCarro) -> bool:
        return self.tipo is None or self.tipo == tipo


# El digitador ve el menú completo de sus carros; los demás, todo menos cargar.
_COMPLETO = (True, True, True)
_SIN_CARGAR = (False, True, True)


def _de(tipo: TipoCarro | None, funciones: tuple[bool, bool, bool]) -> Permisos:
    return Permisos(tipo, *funciones)


PERMISOS: dict[Rol, Permisos] = {
    Rol.ADMIN: Permisos(None, cargar=True, liberar=True, mantener=True, reportes=True),
    # POY
    Rol.DIGITADOR_POY: _de(TipoCarro.POY, _COMPLETO),
    Rol.INTERMEDIO_POY: _de(TipoCarro.POY, _SIN_CARGAR),
    Rol.EMPACADOR_POY: _de(TipoCarro.POY, _SIN_CARGAR),
    # DTY (Twisting libera los carros de DTY: es quien consume su producto)
    Rol.DIGITADOR_DTY: _de(TipoCarro.DTY, _COMPLETO),
    Rol.EMPACADOR_DTY: _de(TipoCarro.DTY, _SIN_CARGAR),
    Rol.TWISTING: _de(TipoCarro.DTY, _SIN_CARGAR),
    # Twisting
    Rol.DIGITADOR_TWT: _de(TipoCarro.TWISTING, _COMPLETO),
    Rol.EMPACADOR_TWT: _de(TipoCarro.TWISTING, _SIN_CARGAR),
    # Nombres anteriores: se conservan para no romper a los usuarios ya creados.
    Rol.POY: _de(TipoCarro.POY, _COMPLETO),  # = digitador POY
    Rol.DTY: _de(TipoCarro.DTY, _COMPLETO),  # = digitador DTY
    # Almacén recibía carros de cualquier proceso. Se deja igual hasta decidir si se retira.
    Rol.ALMACEN: Permisos(None, cargar=False, liberar=True, mantener=False),
}
