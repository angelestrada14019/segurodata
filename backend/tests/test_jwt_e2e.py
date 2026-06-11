"""Pre-mortem E3 — JWT end-to-end contra Supabase REAL.

Verifica la cadena completa: sign-in en Supabase Auth → access_token →
el backend lo decodifica y acepta. Se corre UNA vez antes de la Fase 3
del cronograma y se guarda la evidencia.

Requisitos (variables de entorno):
    E2E_SUPABASE_URL      https://pluxaelenhkdaakxdrpm.supabase.co
    E2E_ANON_KEY          anon key del proyecto
    E2E_EMAIL             usuario de prueba creado en Supabase Auth
    E2E_PASSWORD          su contraseña
    SUPABASE_JWT_SECRET   JWT secret real (Dashboard → Settings → API)

Ejecución:
    python -m pytest tests/test_jwt_e2e.py -m integration -v
"""

import os

import httpx
import pytest

pytestmark = pytest.mark.integration

REQUERIDAS = ["E2E_SUPABASE_URL", "E2E_ANON_KEY", "E2E_EMAIL", "E2E_PASSWORD"]
faltantes = [v for v in REQUERIDAS if not os.environ.get(v)]


@pytest.mark.skipif(bool(faltantes), reason=f"Faltan credenciales E2E: {faltantes}")
async def test_jwt_supabase_end_to_end(client):
    # 1. Sign-in real contra Supabase Auth (password grant)
    url = os.environ["E2E_SUPABASE_URL"]
    resp = httpx.post(
        f"{url}/auth/v1/token?grant_type=password",
        headers={"apikey": os.environ["E2E_ANON_KEY"]},
        json={"email": os.environ["E2E_EMAIL"], "password": os.environ["E2E_PASSWORD"]},
        timeout=15,
    )
    assert resp.status_code == 200, f"Sign-in falló: {resp.text}"
    token = resp.json()["access_token"]

    # 2. El backend decodifica el token real y NO devuelve 401
    r = await client.post(
        "/predict",
        json={"upz_cod": "044", "anio": 2026, "mes": 7},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code != 401, f"E3 FALLÓ — el backend rechazó un token válido: {r.text}"
    # 200 (datos) o 404 (sin fila) son aceptables; 401 es el fallo del pre-mortem
    assert r.status_code in (200, 404, 403)
