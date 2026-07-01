"""PATCH /admin/usuarios/{user_id}/cuadrante — pre-mortem T5 (solo ADMIN)."""

BODY = {"cuadrante_id": "E08C07061"}


async def test_admin_asigna_cuadrante_ok(client, auth_headers):
    resp = await client.patch(
        "/admin/usuarios/user-comandante/cuadrante",
        json=BODY,
        headers=auth_headers("ADMIN"),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"user_id": "user-comandante", "cuadrante_asignado": "E08C07061"}


async def test_admin_sin_token_401(client):
    resp = await client.patch("/admin/usuarios/user-comandante/cuadrante", json=BODY)
    assert resp.status_code == 401


async def test_admin_rol_no_admin_403(client, auth_headers):
    resp = await client.patch(
        "/admin/usuarios/user-comandante/cuadrante",
        json=BODY,
        headers=auth_headers("COMANDANTE_CAI", cuadrante_asignado="E08C07061"),
    )
    assert resp.status_code == 403


async def test_admin_cuadrante_inexistente_404(client, auth_headers):
    resp = await client.patch(
        "/admin/usuarios/user-comandante/cuadrante",
        json={"cuadrante_id": "NO_EXISTE"},
        headers=auth_headers("ADMIN"),
    )
    assert resp.status_code == 404
    assert "cuadrante" in resp.json()["detalle"].lower()


async def test_admin_usuario_inexistente_404(client, auth_headers):
    resp = await client.patch(
        "/admin/usuarios/no-existe-en-user-profiles/cuadrante",
        json=BODY,
        headers=auth_headers("ADMIN"),
    )
    assert resp.status_code == 404
    assert "usuario" in resp.json()["detalle"].lower()
