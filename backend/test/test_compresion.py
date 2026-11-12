def test_las_respuestas_grandes_se_comprimen_si_el_cliente_lo_acepta(client, crear_carro):
    for numero in range(60):
        crear_carro(f"C-{numero:03d}")

    respuesta = client.get("/carros", headers={"Accept-Encoding": "gzip"})

    assert respuesta.status_code == 200
    assert respuesta.headers["content-encoding"] == "gzip"
    assert len(respuesta.json()) == 60


def test_no_se_comprime_si_el_cliente_no_lo_pide(client, crear_carro):
    for numero in range(60):
        crear_carro(f"C-{numero:03d}")

    respuesta = client.get("/carros", headers={"Accept-Encoding": "identity"})

    assert "content-encoding" not in respuesta.headers
