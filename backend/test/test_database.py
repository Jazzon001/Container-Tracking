import pytest

from app.database import normalizar_url


@pytest.mark.parametrize("original", ["postgresql://usuario:clave@servidor:5432/postgres", "postgres://usuario:clave@servidor:5432/postgres"])
def test_las_urls_de_postgresql_usan_el_driver_psycopg(original):
    assert normalizar_url(original) == "postgresql+psycopg://usuario:clave@servidor:5432/postgres"


def test_una_url_que_ya_indica_el_driver_no_se_modifica():
    url = "postgresql+psycopg://usuario:clave@servidor:5432/postgres"
    assert normalizar_url(url) == url


def test_las_urls_de_sqlite_no_se_modifican():
    assert normalizar_url("sqlite:///./container_tracking.db") == "sqlite:///./container_tracking.db"


def test_conserva_los_caracteres_especiales_de_la_clave():
    original = "postgresql://postgres.abc:p%40ss%2Fw0rd@host:5432/postgres?sslmode=require"
    assert normalizar_url(original).endswith("p%40ss%2Fw0rd@host:5432/postgres?sslmode=require")
