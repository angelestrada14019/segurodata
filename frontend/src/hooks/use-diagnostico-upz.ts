import { useQuery } from "@tanstack/react-query";
import { usePredict } from "@/hooks/use-predict";
import { useExplain } from "@/hooks/use-explain";
import { obtenerPeriodoMasReciente } from "@/lib/periodo-predicciones";
import { queryKeys } from "@/lib/query-keys";

/**
 * Agrupa `usePredict` + `useExplain` para el período (anio, mes) VIGENTE —
 * mismo criterio de resolución de período que `use-upz-geometrias.ts` /
 * `use-localidades-geometrias.ts`: primero se resuelve el mes más reciente
 * disponible en `predicciones` (RPC `periodo_mas_reciente`, ver
 * `lib/periodo-predicciones.ts`), y solo entonces se disparan /predict y
 * /explain — nunca se llaman con anio/mes sin resolver.
 *
 * A diferencia de las geometrías (una sola llamada que depende del período),
 * aquí dos llamadas independientes (`/predict`, `/explain`) dependen del
 * mismo período resuelto, así que el período se cachea como query propia
 * (`queryKeys.periodoVigente`) en vez de resolverse por duplicado dentro de
 * cada queryFn — evita dos round-trips idénticos a la RPC.
 *
 * Consumido por `components/modal-upz/modal-upz.tsx` (pestaña Predicción,
 * y de ahí el `shap_top3` viaja por prop a la pestaña Sugerencia).
 */
export function useDiagnosticoUpz(upzCod: string, habilitado = true) {
  const periodoQuery = useQuery({
    queryKey: queryKeys.periodoVigente,
    queryFn: obtenerPeriodoMasReciente,
    enabled: habilitado,
    staleTime: 5 * 60_000,
  });

  const periodo = periodoQuery.data;
  const listoParaConsultar = habilitado && !!periodo;

  const prediccionQuery = usePredict(
    upzCod,
    periodo?.anio ?? 0,
    periodo?.mes ?? 0,
    listoParaConsultar,
  );
  const explicacionQuery = useExplain(
    upzCod,
    periodo?.anio ?? 0,
    periodo?.mes ?? 0,
    listoParaConsultar,
  );

  return {
    prediccion: prediccionQuery.data,
    explicacion: explicacionQuery.data,
    isLoading:
      periodoQuery.isLoading ||
      (listoParaConsultar &&
        (prediccionQuery.isLoading || explicacionQuery.isLoading)),
    /** No forma parte del contrato mínimo pedido pero evita fallos silenciosos
     * (404 sin predicción / 403 fuera de cuadrante) — ver tab-prediccion.tsx. */
    error: periodoQuery.error ?? prediccionQuery.error ?? explicacionQuery.error ?? null,
  };
}
