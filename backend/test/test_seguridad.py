from datetime import timedelta

import pytest

from app.errores import NoAutenticado
from app.seguridad import crear_token, hashear_password, leer_token, verificar_password


def test_el_hash_no_contiene_la_contrasena():
    assert "clave-segura-123" not in hashear_password("clave-segura-123")


def test_misma_contrasena_genera_hashes_distintos():
    assert hashear_password("clave-segura-123") != hashear_password("clave-segura-123")


def test_verifica_la_contrasena_correcta_y_rechaza_la_incorrecta():
    almacenado = hashear_password("clave-segura-123")
    assert verificar_password("clave-segura-123", almacenado)
    assert not verificar_password("otra-clave-456", almacenado)


def test_un_hash_con_formato_invalido_no_verifica():
    assert not verificar_password("clave-segura-123", "esto-no-es-un-hash")


def test_el_token_devuelve_el_usuario_que_lo_creo():
    assert leer_token(crear_token("maria")) == "maria"


def test_un_token_vencido_se_rechaza():
    token = crear_token("maria", duracion=timedelta(seconds=-1))
    with pytest.raises(NoAutenticado):
        leer_token(token)


def test_un_token_manipulado_se_rechaza():
    with pytest.raises(NoAutenticado):
        leer_token(crear_token("maria") + "x")


def test_un_token_firmado_con_otra_clave_se_rechaza(monkeypatch):
    token = crear_token("maria")
    monkeypatch.setenv("JWT_SECRET", "otra-clave-distinta-de-32-caracteres-xx")
    with pytest.raises(NoAutenticado):
        leer_token(token)


def test_sin_jwt_secret_se_falla_con_un_mensaje_claro(monkeypatch):
    monkeypatch.delenv("JWT_SECRET")
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        crear_token("maria")
