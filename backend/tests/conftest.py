"""Fixtures de la suite — app con dependency_overrides (fakes) + token_factory.

La decodificación JWT es REAL (PyJWT con secret de test); solo los datos son fake.
Ningún unit test toca la red.
"""

import os
import time

# Entorno de test ANTES de importar la app (Settings se evalúa al importar)
os.environ["ENV"] = "test"
os.environ["AUTH_MODE"] = "enabled"
os.environ["SUPABASE_JWT_SECRET"] = "test-secret-segurodata-0123456789abcdef"
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_SERVICE_KEY"] = ""
os.environ["SUPABASE_JWKS_URL"] = ""
os.environ["OPENROUTER_API_KEY"] = ""

import jwt  # noqa: E402
import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.config import get_settings  # noqa: E402

get_settings.cache_clear()

from app import dependencies  # noqa: E402
from app.exceptions import UpstreamError  # noqa: E402
from app.main import create_app  # noqa: E402
from app.repositories.ontology_repo import OntologyRepo  # noqa: E402

TEST_SECRET = "test-secret-segurodata-0123456789abcdef"

PREDICCION_044 = {
    "upz_cod": "044",
    "anio": 2026,
    "mes": 7,
    "nivel_riesgo": "ALTO",
    "prob_critico": 0.08,
    "prob_alto": 0.62,
    "prob_medio": 0.24,
    "prob_bajo": 0.06,
    "origen": "seed_dev",
}

SHAP_044 = [
    {"feature": "cuadrantes_por_km2", "valor": -0.34},
    {"feature": "n_delitos_upz_4sem", "valor": 0.28},
    {"feature": "luminarias_led_upz", "valor": -0.19},
    {"feature": "estrato_promedio_upz", "valor": 0.11},
    {"feature": "n_camaras_upz", "valor": -0.09},
    {"feature": "ratio_nuse_criminal_upz", "valor": 0.07},
    {"feature": "temperatura_c", "valor": 0.03},
    {"feature": "dist_tm_metros", "valor": 0.01},
]

CHUNKS = [
    {
        "id": 1,
        "content": "El boletín SCJ de noviembre reporta aumento de hurto en Kennedy por receptación.",
        "source": "SCJ_BOLETIN",
        "titulo": "Boletín SCJ nov-2025",
        "fecha": "2025-11-01",
        "url": None,
        "similarity": 0.83,
    },
    {
        "id": 2,
        "content": "Noticia: operativo contra banda dedicada al hurto de celulares en Américas.",
        "source": "RSS_ELTIEMPO",
        "titulo": "Operativo en Américas",
        "fecha": "2025-10-15",
        "url": "https://eltiempo.com/x",
        "similarity": 0.78,
    },
]


class FakePredictionsRepo:
    async def get(self, upz_cod, anio, mes):
        if (upz_cod, anio, mes) == ("044", 2026, 7):
            return dict(PREDICCION_044)
        return None


class FakeShapRepo:
    async def get_values(self, upz_cod, anio, mes):
        if (upz_cod, anio, mes) == ("044", 2026, 7):
            return sorted(SHAP_044, key=lambda f: abs(f["valor"]), reverse=True)
        return []


class FakeCuadrantesRepo:
    UPZS = {"E08C07061": ["043", "044"]}

    async def get_upzs(self, cuadrante_id):
        return self.UPZS.get(cuadrante_id, [])

    async def find_cai_para_upz(self, upz_cod):
        if upz_cod == "044":
            return {
                "cuadrante_id": "E08C07061",
                "nom_cai": "PLAZA DE LAS AMERICAS",
                "telefono": "3017565440",
            }
        return None


class FakeDocumentsRepo:
    def __init__(self):
        self.llamadas = []

    async def match(self, embedding, threshold=0.7, count=5, filter_upz=None):
        self.llamadas.append({"threshold": threshold, "filter_upz": filter_upz})
        if filter_upz == "999":  # UPZ sin documentos — fuerza el retry sin filtro
            return []
        return list(CHUNKS)


class FakeEmbeddings:
    async def encode(self, texto):
        return [0.1] * 384


class FakeOpenRouter:
    """LLM simulado; con fallar=True simula caída de OpenRouter (cuota agotada)."""

    def __init__(self, fallar=False):
        self.fallar = fallar
        self.configurado = not fallar

    async def chat(self, messages, model=None):
        if self.fallar:
            raise UpstreamError("OpenRouter simulado caído")
        return "Respuesta operacional simulada citando [1] y [2].", "fake/modelo", False


@pytest.fixture(scope="session")
def fakes():
    return {
        "predictions": FakePredictionsRepo(),
        "shap": FakeShapRepo(),
        "cuadrantes": FakeCuadrantesRepo(),
        "documents": FakeDocumentsRepo(),
        "embeddings": FakeEmbeddings(),
        "openrouter": FakeOpenRouter(),
        "ontology": OntologyRepo(""),
    }


@pytest.fixture(scope="session")
def app(fakes):
    application = create_app()
    application.dependency_overrides[dependencies.get_predictions_repo] = lambda: fakes[
        "predictions"
    ]
    application.dependency_overrides[dependencies.get_shap_repo] = lambda: fakes["shap"]
    application.dependency_overrides[dependencies.get_cuadrantes_repo] = lambda: fakes["cuadrantes"]
    application.dependency_overrides[dependencies.get_documents_repo] = lambda: fakes["documents"]
    application.dependency_overrides[dependencies.get_embeddings] = lambda: fakes["embeddings"]
    application.dependency_overrides[dependencies.get_openrouter] = lambda: fakes["openrouter"]
    application.dependency_overrides[dependencies.get_ontology] = lambda: fakes["ontology"]
    return application


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture(scope="session")
def token_factory():
    """Firma JWTs HS256 reales con el secret de test — la verificación es genuina."""

    def _crear(rol="CIUDADANO", cuadrante_asignado=None, incluir_rol=True, secret=TEST_SECRET):
        payload = {
            "sub": f"user-{rol.lower()}",
            "email": f"{rol.lower()}@test.local",
            "aud": "authenticated",
            "exp": int(time.time()) + 3600,
        }
        if incluir_rol:
            payload["rol"] = rol
        if cuadrante_asignado is not None:
            payload["cuadrante_asignado"] = cuadrante_asignado
        return jwt.encode(payload, secret, algorithm="HS256")

    return _crear


@pytest.fixture(scope="session")
def auth_headers(token_factory):
    def _headers(rol="CIUDADANO", cuadrante_asignado=None, **kwargs):
        token = token_factory(rol=rol, cuadrante_asignado=cuadrante_asignado, **kwargs)
        return {"Authorization": f"Bearer {token}"}

    return _headers
