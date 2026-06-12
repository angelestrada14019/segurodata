PARAMS = {"upz_cod": "044", "anio": 2026, "mes": 7}


async def test_explain_sin_token_401(client):
    resp = await client.get("/explain", params=PARAMS)
    assert resp.status_code == 401


async def test_explain_ciudadano_solo_top3(client, auth_headers):
    resp = await client.get("/explain", params=PARAMS, headers=auth_headers("CIUDADANO"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["nivel_riesgo"] == "ALTO"
    assert len(data["shap_top3"]) == 3
    assert data["shap_top3"][0]["feature"] == "cuadrantes_por_km2"  # mayor |valor|
    assert "shap_completo" not in data  # detalle completo solo ANALISTA/ADMIN


async def test_explain_analista_detalle_completo(client, auth_headers):
    resp = await client.get("/explain", params=PARAMS, headers=auth_headers("ANALISTA_SDSCJ"))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["shap_completo"]) == 8
    assert len(data["shap_top3"]) == 3


async def test_explain_comandante_fuera_de_cuadrante_403(client, auth_headers):
    headers = auth_headers("COMANDANTE_CAI", cuadrante_asignado="E08C07061")
    resp = await client.get(
        "/explain", params={"upz_cod": "099", "anio": 2026, "mes": 7}, headers=headers
    )
    assert resp.status_code == 403


async def test_explain_sin_datos_404(client, auth_headers):
    resp = await client.get(
        "/explain",
        params={"upz_cod": "099", "anio": 2026, "mes": 1},
        headers=auth_headers("ADMIN"),
    )
    assert resp.status_code == 404
