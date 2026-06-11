PREGUNTA = {"pregunta": "¿Por qué aumentó el hurto en Kennedy?", "upz_contexto": "044"}


async def test_graphrag_sin_token_401(client):
    resp = await client.post("/graphrag", json=PREGUNTA)
    assert resp.status_code == 401


async def test_graphrag_responde_con_fuentes(client, auth_headers):
    resp = await client.post("/graphrag", json=PREGUNTA, headers=auth_headers("CIUDADANO"))
    assert resp.status_code == 200
    data = resp.json()
    assert "[1]" in data["respuesta"]
    assert len(data["fuentes"]) == 2
    assert data["fuentes"][0]["tipo"] == "SCJ_BOLETIN"
    assert data["modelo_llm"] == "fake/modelo"
    assert data["cacheado"] is False


async def test_graphrag_retry_sin_filtro_cuando_upz_sin_docs(client, auth_headers, fakes):
    """Si el filtro por UPZ da 0 chunks, reintenta sin filtro — nunca respuesta vacía."""
    fakes["documents"].llamadas.clear()
    body = {"pregunta": "¿Qué pasa con el hurto aquí?", "upz_contexto": "999"}
    resp = await client.post("/graphrag", json=body, headers=auth_headers("CIUDADANO"))
    assert resp.status_code == 200
    assert len(resp.json()["fuentes"]) == 2
    filtros = [c["filter_upz"] for c in fakes["documents"].llamadas]
    assert filtros[0] == "999" and None in filtros[1:]


async def test_graphrag_pregunta_corta_422(client, auth_headers):
    resp = await client.post(
        "/graphrag", json={"pregunta": "hm"}, headers=auth_headers("CIUDADANO")
    )
    assert resp.status_code == 422
