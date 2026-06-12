BODY_044 = {"upz_cod": "044", "anio": 2026, "mes": 7}


async def test_predict_sin_token_401(client):
    resp = await client.post("/predict", json=BODY_044)
    assert resp.status_code == 401


async def test_predict_token_invalido_401(client):
    resp = await client.post(
        "/predict", json=BODY_044, headers={"Authorization": "Bearer basura.no.jwt"}
    )
    assert resp.status_code == 401


async def test_predict_admin_ok(client, auth_headers):
    resp = await client.post("/predict", json=BODY_044, headers=auth_headers("ADMIN"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["nivel_riesgo"] == "ALTO"
    assert data["origen"] == "seed_dev"
    suma = sum(data["probabilidades"].values())
    assert abs(suma - 1.0) < 0.01
    assert set(data["probabilidades"]) == {"CRITICO", "ALTO", "MEDIO", "BAJO"}


async def test_predict_ciudadano_ok(client, auth_headers):
    resp = await client.post("/predict", json=BODY_044, headers=auth_headers("CIUDADANO"))
    assert resp.status_code == 200


async def test_predict_sin_datos_404(client, auth_headers):
    resp = await client.post(
        "/predict",
        json={"upz_cod": "099", "anio": 2026, "mes": 1},
        headers=auth_headers("ADMIN"),
    )
    assert resp.status_code == 404


async def test_predict_comandante_dentro_de_su_cuadrante(client, auth_headers):
    headers = auth_headers("COMANDANTE_CAI", cuadrante_asignado="E08C07061")
    resp = await client.post("/predict", json=BODY_044, headers=headers)
    assert resp.status_code == 200


async def test_predict_comandante_fuera_de_cuadrante_403(client, auth_headers):
    """D8: el filtro vive en la capa services, no en RLS (la service key la bypasea)."""
    headers = auth_headers("COMANDANTE_CAI", cuadrante_asignado="E08C07061")
    resp = await client.post(
        "/predict", json={"upz_cod": "099", "anio": 2026, "mes": 7}, headers=headers
    )
    assert resp.status_code == 403
    assert "fuera del cuadrante" in resp.json()["detalle"]


async def test_predict_comandante_sin_cuadrante_403(client, auth_headers):
    headers = auth_headers("COMANDANTE_CAI")  # sin claim cuadrante_asignado
    resp = await client.post("/predict", json=BODY_044, headers=headers)
    assert resp.status_code == 403
    assert "sin cuadrante" in resp.json()["detalle"].lower()


async def test_predict_upz_invalida_422(client, auth_headers):
    resp = await client.post(
        "/predict", json={"upz_cod": "44", "anio": 2026, "mes": 7}, headers=auth_headers("ADMIN")
    )
    assert resp.status_code == 422
