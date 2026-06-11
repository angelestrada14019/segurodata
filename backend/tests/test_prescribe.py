from app.repositories.ontology_repo import OntologyRepo
from app.services.prescribe_service import PrescribeService

BODY = {
    "upz_cod": "044",
    "shap_top": [
        {"feature": "cuadrantes_por_km2", "valor": -0.34},
        {"feature": "n_delitos_upz_4sem", "valor": 0.28},
    ],
}


async def test_prescribe_ciudadano_403(client, auth_headers):
    resp = await client.post("/prescribe", json=BODY, headers=auth_headers("CIUDADANO"))
    assert resp.status_code == 403


async def test_prescribe_sin_token_401(client):
    resp = await client.post("/prescribe", json=BODY)
    assert resp.status_code == 401


async def test_prescribe_admin_ok(client, auth_headers):
    resp = await client.post("/prescribe", json=BODY, headers=auth_headers("ADMIN"))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["diagnosticos"]) == 2
    assert data["diagnosticos"][0]["entidad_responsable"] == "MEBOG / SIJIN"
    assert data["cai"]["nombre"] == "PLAZA DE LAS AMERICAS"
    assert data["cai"]["telefono"] == "3017565440"
    assert data["recomendacion_llm"]


async def test_prescribe_comandante_su_cuadrante_ok(client, auth_headers):
    headers = auth_headers("COMANDANTE_CAI", cuadrante_asignado="E08C07061")
    resp = await client.post("/prescribe", json=BODY, headers=headers)
    assert resp.status_code == 200


async def test_prescribe_feature_desconocida_sin_diagnosticos(client, auth_headers):
    body = {"upz_cod": "044", "shap_top": [{"feature": "feature_inventada", "valor": 0.5}]}
    resp = await client.post("/prescribe", json=body, headers=auth_headers("ADMIN"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["diagnosticos"] == []
    assert "ontológica" in data["recomendacion_llm"]


async def test_mapeo_ontologico_determinista_sin_llm(fakes):
    """D10: el mapeo feature→entidad es lookup puro — el test no necesita LLM vivo.
    Con OpenRouter caído, /prescribe degrada al texto determinista."""
    from tests.conftest import FakeOpenRouter

    service = PrescribeService(
        ontology=OntologyRepo(""),
        cuadrantes=fakes["cuadrantes"],
        openrouter=FakeOpenRouter(fallar=True),
    )
    from app.core.security import UserClaims

    admin = UserClaims(
        sub="t", email="t@t", rol="ADMIN", cuadrante_asignado=None, rol_desde_claims=True
    )
    resultado = await service.prescribe(
        admin, "044", [{"feature": "luminarias_led_upz", "valor": -0.2}]
    )
    assert resultado["diagnosticos"][0]["entidad_responsable"] == "UAESP"
    assert resultado["modelo_llm"] is None  # LLM caído → fallback determinista
    assert "UAESP" in resultado["recomendacion_llm"]
    assert "PLAZA DE LAS AMERICAS" in resultado["recomendacion_llm"]


def test_tabla_ontologica_17_filas():
    repo = OntologyRepo("")
    assert len(repo.todas()) == 17
    features = {f["feature"] for f in repo.todas()}
    assert {
        "cuadrantes_por_km2",
        "luminarias_led_upz",
        "n_camaras_upz",
        "km_via_intervenida_upz",
        "ratio_nuse_criminal_upz",
    } <= features
