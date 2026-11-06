"""Errores de negocio de la aplicación.

Cada error declara el código HTTP con el que se responde. Así, agregar un error
nuevo no obliga a tocar el manejador de errores de `main.py`.
"""


class ErrorDeNegocio(Exception):
    """Base de los errores que la API traduce a una respuesta HTTP."""

    codigo_http = 400


class CarroNoEncontrado(ErrorDeNegocio):
    codigo_http = 404

    def __init__(self) -> None:
        super().__init__("Carro no encontrado")


class EstadoInvalido(ErrorDeNegocio):
    codigo_http = 409

    def __init__(self, detalle: str) -> None:
        super().__init__(detalle)


class ContenedorEnUso(ErrorDeNegocio):
    codigo_http = 409

    def __init__(self) -> None:
        super().__init__("Ese contenedor elemento ya está asignado a otro carro")


class NoAutenticado(ErrorDeNegocio):
    codigo_http = 401

    def __init__(self, detalle: str = "Debes iniciar sesión") -> None:
        super().__init__(detalle)


class CredencialesInvalidas(ErrorDeNegocio):
    codigo_http = 401

    def __init__(self) -> None:
        super().__init__("Usuario o contraseña incorrectos")


class SinPermiso(ErrorDeNegocio):
    codigo_http = 403

    def __init__(self) -> None:
        super().__init__("No tienes permiso para esta operación")


class UsuarioExistente(ErrorDeNegocio):
    codigo_http = 409

    def __init__(self) -> None:
        super().__init__("Ya existe un usuario con ese nombre")
