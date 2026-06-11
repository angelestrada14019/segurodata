"""Pre-mortem T5: /whoami detecta al comandante sin cuadrante asignado
para que el frontend muestre un aviso en vez de un mapa vacío silencioso."""


async def test_whoami_sin_token_401(client):
    resp = await client.get("/whoami")
    assert resp.status_code == 401


async def test_whoami_comandante_sin_cuadrante_pendiente_true(client, auth_headers):
    resp = await client.get("/whoami", headers=auth_headers("COMANDANTE_CAI"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["rol"] == "COMANDANTE_CAI"
    assert data["cuadrante_asignado"] is None
    assert data["cuadrante_pendiente"] is True


async def test_whoami_comandante_con_cuadrante_pendiente_false(client, auth_headers):
    headers = auth_headers("COMANDANTE_CAI", cuadrante_asignado="E08C07061")
    resp = await client.get("/whoami", headers=headers)
    data = resp.json()
    assert data["cuadrante_asignado"] == "E08C07061"
    assert data["cuadrante_pendiente"] is False


async def test_whoami_ciudadano(client, auth_headers):
    resp = await client.get("/whoami", headers=auth_headers("CIUDADANO"))
    data = resp.json()
    assert data["rol"] == "CIUDADANO"
    assert data["cuadrante_pendiente"] is False


async def test_whoami_token_sin_claim_rol_cae_a_ciudadano(client, auth_headers):
    """Si el custom_access_token_hook no está habilitado, el token no trae rol:
    el backend degrada a CIUDADANO (sin Supabase en test no hay fallback a perfil)."""
    resp = await client.get("/whoami", headers=auth_headers("ADMIN", incluir_rol=False))
    assert resp.status_code == 200
    assert resp.json()["rol"] == "CIUDADANO"
