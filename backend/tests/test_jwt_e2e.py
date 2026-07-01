"""Pre-mortem E3 — JWT end-to-end contra Supabase REAL.

Verifica la cadena completa: sign-in en Supabase Auth → access_token →
el backend lo decodifica y acepta. Se corre UNA vez antes de la Fase 3
del cronograma y se guarda la evidencia.

Requisitos (variables de entorno):
    E2E_SUPABASE_URL      https://pluxaelenhkdaakxdrpm.supabase.co
    E2E_ANON_KEY          anon key del proyecto
    E2E_EMAIL             usuario de prueba creado en Supabase Auth
    E2E_PASSWORD          su contraseña

El proyecto real firma con ES256 (JWKS), no HS256 — por eso este test NO
reutiliza el fixture `client` (su app está fijada a HS256 + secret de test
para el resto de la suite). Construye su propia app con `SUPABASE_JWKS_URL`
apuntando al JWKS real, dejando `SUPABASE_JWT_SECRET` vacío para forzar la
rama ES256/RS256 de `decode_supabase_jwt`.

Ejecución:
    python -m pytest tests/test_jwt_e2e.py -m integration -v
"""

import os

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from app import dependencies
from app.config import Settings, get_settings
from app.main import create_app

pytestmark = pytest.mark.integration

REQUERIDAS = ["E2E_SUPABASE_URL", "E2E_ANON_KEY", "E2E_EMAIL", "E2E_PASSWORD"]
faltantes = [v for v in REQUERIDAS if not os.environ.get(v)]


@pytest.mark.skipif(bool(faltantes), reason=f"Faltan credenciales E2E: {faltantes}")
async def test_jwt_supabase_end_to_end(fakes):
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

    # 2. App con settings ES256/JWKS reales (no la del fixture `client`, que es HS256 de test)
    settings_reales = Settings(
        env="test",
        auth_mode="enabled",
        supabase_jwt_secret="",
        supabase_jwks_url=f"{url}/auth/v1/.well-known/jwks.json",
    )
    e2e_app = create_app()
    e2e_app.dependency_overrides[get_settings] = lambda: settings_reales
    e2e_app.dependency_overrides[dependencies.get_predictions_repo] = lambda: fakes["predictions"]
    e2e_app.dependency_overrides[dependencies.get_cuadrantes_repo] = lambda: fakes["cuadrantes"]

    transport = ASGITransport(app=e2e_app)
    async with AsyncClient(transport=transport, base_url="http://test") as e2e_client:
        r = await e2e_client.post(
            "/predict",
            json={"upz_cod": "044", "anio": 2026, "mes": 7},
            headers={"Authorization": f"Bearer {token}"},
        )

    # El backend decodifica el token real y NO devuelve 401.
    # 200 (datos) o 404 (sin fila) son aceptables; 401 es el fallo del pre-mortem
    assert r.status_code != 401, f"E3 FALLÓ — el backend rechazó un token válido: {r.text}"
    assert r.status_code in (200, 404, 403)
