"""Lógica de /prescribe — tabla ontológica determinista + redacción LLM.

El mapeo feature→diagnóstico→entidad→acción es un lookup puro (D10, testeable
sin LLM). El LLM solo redacta la recomendación final con los datos del CAI.
"""

import structlog

from app.clients.openrouter_client import OpenRouterClient
from app.core.security import UserClaims
from app.exceptions import UpstreamError
from app.repositories.cuadrantes_repo import CuadrantesRepo
from app.repositories.ontology_repo import OntologyRepo
from app.services.prediction_service import verificar_acceso_upz

logger = structlog.get_logger("prescribe")

SYSTEM_PROMPT = (
    "Eres el asistente operacional de SeguroData Bogotá. Redacta una recomendación "
    "para el comandante del CAI en español operacional (sin jerga de ML), máximo "
    "200 palabras, en tono directo y accionable. Incluye: la situación, las acciones "
    "concretas con su entidad responsable, y el contacto del CAI si se proporciona. "
    "No inventes datos que no estén en el resumen."
)


class PrescribeService:
    def __init__(
        self,
        ontology: OntologyRepo,
        cuadrantes: CuadrantesRepo,
        openrouter: OpenRouterClient,
    ):
        self._ontology = ontology
        self._cuadrantes = cuadrantes
        self._openrouter = openrouter

    async def prescribe(self, claims: UserClaims, upz_cod: str, shap_top: list[dict]) -> dict:
        await verificar_acceso_upz(claims, upz_cod, self._cuadrantes)

        # 1. Mapeo ontológico DETERMINISTA (sin LLM)
        diagnosticos = []
        for item in shap_top:
            fila = self._ontology.get(item["feature"])
            if fila is None:
                logger.warning("feature_sin_ontologia", feature=item["feature"])
                continue
            diagnosticos.append(
                {
                    "feature": fila["feature"],
                    "diagnostico": fila["diagnostico"],
                    "tipo_intervencion": fila["tipo_intervencion"],
                    "entidad_responsable": fila["entidad_responsable"],
                    "accion": fila["accion"],
                }
            )

        # 2. CAI responsable de la UPZ (F4)
        cai_fila = await self._cuadrantes.find_cai_para_upz(upz_cod)
        cai = (
            {
                "cuadrante_id": cai_fila["cuadrante_id"],
                "nombre": cai_fila["nom_cai"],
                "telefono": cai_fila.get("telefono"),
            }
            if cai_fila
            else None
        )

        # 3. Redacción LLM (con fallback determinista si OpenRouter falla)
        recomendacion, modelo = await self._redactar(upz_cod, diagnosticos, cai)
        return {
            "upz_cod": upz_cod,
            "diagnosticos": diagnosticos,
            "cai": cai,
            "recomendacion_llm": recomendacion,
            "modelo_llm": modelo,
        }

    async def _redactar(
        self, upz_cod: str, diagnosticos: list[dict], cai: dict | None
    ) -> tuple[str, str | None]:
        if not diagnosticos:
            return (
                f"UPZ {upz_cod}: las features recibidas no tienen mapeo en la tabla "
                "ontológica — revisar el top SHAP enviado.",
                None,
            )
        resumen = "\n".join(
            f"- {d['diagnostico']} → {d['entidad_responsable']}: {d['accion']}"
            for d in diagnosticos
        )
        fallback = f"UPZ {upz_cod} — acciones recomendadas:\n{resumen}"
        if cai:
            fallback += f"\nCAI responsable: {cai['nombre']}"
            if cai.get("telefono"):
                fallback += f" (tel. {cai['telefono']})"

        try:
            user_msg = f"UPZ {upz_cod} de Bogotá.\nDiagnósticos y acciones:\n{resumen}"
            if cai:
                user_msg += (
                    f"\nCAI responsable: {cai['nombre']}, teléfono {cai.get('telefono', 'N/D')}"
                )
            texto, modelo, _ = await self._openrouter.chat(
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ]
            )
            return texto, modelo
        except UpstreamError as exc:
            logger.warning("prescribe_sin_llm", motivo=exc.message)
            return fallback, None
