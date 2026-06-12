"""Tabla ontológica prescriptiva (D10) — JSON estático en memoria, 17 filas.

Mapeo DETERMINISTA: feature SHAP → diagnóstico → entidad responsable → acción.
El LLM solo redacta; jamás decide el mapeo. Override vía TABLA_ONTOLOGICA_PATH
cuando el Notebook 03 genere la versión definitiva.
"""

import json
from pathlib import Path

import structlog

logger = structlog.get_logger("ontologia")

_BUNDLED = Path(__file__).resolve().parents[1] / "data" / "tabla_ontologica_seed.json"


class OntologyRepo:
    def __init__(self, path_override: str = ""):
        path = Path(path_override) if path_override else _BUNDLED
        with open(path, encoding="utf-8") as f:
            filas: list[dict] = json.load(f)
        self._por_feature: dict[str, dict] = {fila["feature"]: fila for fila in filas}
        logger.info("ontologia_cargada", filas=len(filas), origen=str(path))

    def get(self, feature: str) -> dict | None:
        return self._por_feature.get(feature)

    def todas(self) -> list[dict]:
        return list(self._por_feature.values())
