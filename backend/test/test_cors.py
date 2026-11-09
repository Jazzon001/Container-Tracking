def preflight(cliente, origen):
    return cliente.options(
        "/auth/login",
        headers={
            "Origin": origen,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )


def test_permite_al_frontend_local_llamar_a_la_api(cliente_anonimo):
    respuesta = preflight(cliente_anonimo, "http://localhost:4200")
    assert respuesta.status_code == 200
    assert respuesta.headers["access-control-allow-origin"] == "http://localhost:4200"


def test_permite_el_encabezado_de_autorizacion(cliente_anonimo):
    respuesta = preflight(cliente_anonimo, "http://localhost:4200")
    assert "authorization" in respuesta.headers["access-control-allow-headers"].lower()


def test_no_permite_origenes_desconocidos(cliente_anonimo):
    respuesta = preflight(cliente_anonimo, "http://sitio-malicioso.example")
    assert "access-control-allow-origin" not in respuesta.headers
