import { Building2, Loader2, Lock, Phone, RefreshCw, Sparkles } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { usePrescribe } from "@/hooks/use-prescribe";
import { ApiError } from "@/lib/api-client";
import { etiquetaFeature } from "@/lib/features-modelo";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { RolBackend, ShapFeatureValor } from "@/types/api";

interface TabSugerenciaProps {
  upzCod: string;
  shapTop: ShapFeatureValor[] | undefined;
}

const ROLES_CON_ACCESO: RolBackend[] = ["COMANDANTE_CAI", "ANALISTA_SDSCJ", "ADMIN"];

/**
 * Pestaña Sugerencia — POST /prescribe. Usa el `shap_top3` YA resuelto en
 * la pestaña Predicción (recibido por prop desde modal-upz.tsx, que a su
 * vez lo obtiene de `useDiagnosticoUpz`) — nunca vuelve a llamar useExplain
 * aquí. Disparo MANUAL (botón), no automático al abrir la pestaña: es una
 * llamada con costo de LLM (`recomendacion_llm`), no un GET idempotente —
 * auto-disparar en cada visita a la pestaña generaría llamadas repetidas
 * innecesarias (Radix Tabs desmonta el contenido de pestañas inactivas).
 */
export function TabSugerencia({ upzCod, shapTop }: TabSugerenciaProps) {
  const { rol } = useAuth();
  const prescribeMutation = usePrescribe();

  if (!rol || !ROLES_CON_ACCESO.includes(rol)) {
    return (
      <Alert>
        <Lock className="h-4 w-4" aria-hidden="true" />
        <AlertTitle>Disponible solo para roles operacionales</AlertTitle>
        <AlertDescription>
          La recomendación prescriptiva está disponible para Comandante CAI,
          Analista SDSCJ y Admin. Inicia sesión con una cuenta institucional
          para acceder.
        </AlertDescription>
      </Alert>
    );
  }

  if (!shapTop || shapTop.length === 0) {
    return (
      <div
        role="status"
        className="rounded-md border border-dashed border-border p-6 text-center text-sm text-muted-foreground"
      >
        Esperando el análisis SHAP de la pestaña Predicción antes de poder
        generar una recomendación.
      </div>
    );
  }

  // Narrowing explícito: `shapTop` ya no es undefined desde este punto, pero
  // TS no retiene ese narrowing dentro del closure `generar` (parámetro, no
  // const) — se guarda en una constante local para no necesitar `!`.
  const shapTopListo = shapTop;

  function generar() {
    prescribeMutation.mutate({ upz_cod: upzCod, shap_top: shapTopListo });
  }

  if (prescribeMutation.isPending) {
    return (
      <div
        role="status"
        className="flex flex-col items-center gap-3 rounded-md border border-border bg-card p-8 text-center"
      >
        <Loader2 className="h-6 w-6 animate-spin text-primary" aria-hidden="true" />
        <p className="text-sm text-muted-foreground">
          Analizando causas y generando recomendación…
        </p>
      </div>
    );
  }

  if (prescribeMutation.isError) {
    return (
      <div className="flex flex-col gap-3">
        <ErrorPrescribe error={prescribeMutation.error} />
        <Button type="button" variant="outline" onClick={generar} className="w-fit">
          <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
          Reintentar
        </Button>
      </div>
    );
  }

  if (!prescribeMutation.data) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-md border border-dashed border-border p-8 text-center">
        <Sparkles className="h-6 w-6 text-primary" aria-hidden="true" />
        <p className="max-w-sm text-sm text-muted-foreground">
          Genera el diagnóstico causal y la recomendación operacional para
          esta UPZ a partir de las variables que más influyen en su riesgo.
        </p>
        <Button type="button" onClick={generar}>
          <Sparkles className="h-4 w-4" aria-hidden="true" />
          Generar recomendación
        </Button>
      </div>
    );
  }

  const data = prescribeMutation.data;

  return (
    <div className="flex flex-col gap-5">
      <div className="rounded-md border border-primary/40 bg-primary/5 p-4">
        <div className="mb-2 flex items-center gap-2 text-xs font-semibold tracking-wide text-primary uppercase">
          <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
          Recomendación operacional
        </div>
        <p className="text-sm leading-relaxed text-foreground">{data.recomendacion_llm}</p>
      </div>

      <div className="rounded-md border border-border bg-card p-4">
        <div className="mb-2 flex items-center gap-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
          <Building2 className="h-3.5 w-3.5" aria-hidden="true" />
          CAI responsable
        </div>
        <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-sm">
          <span className="font-medium text-foreground">{data.cai.nombre}</span>
          <span className="font-mono-data text-xs text-muted-foreground">
            Cuadrante {data.cai.cuadrante_id}
          </span>
          <span className="flex items-center gap-1.5 text-muted-foreground">
            <Phone className="h-3.5 w-3.5" aria-hidden="true" />
            {data.cai.telefono ?? "No registrado"}
          </span>
        </div>
      </div>

      <div>
        <h3 className="mb-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
          Diagnóstico por variable
        </h3>
        <div className="rounded-md border border-border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Variable</TableHead>
                <TableHead>Diagnóstico</TableHead>
                <TableHead>Tipo de intervención</TableHead>
                <TableHead>Entidad responsable</TableHead>
                <TableHead>Acción</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.diagnosticos.map((d) => (
                <TableRow key={d.feature}>
                  <TableCell className="font-mono-data text-xs whitespace-nowrap">
                    {etiquetaFeature(d.feature)}
                  </TableCell>
                  <TableCell className="text-sm">{d.diagnostico}</TableCell>
                  <TableCell className="text-sm whitespace-nowrap">{d.tipo_intervencion}</TableCell>
                  <TableCell className="text-sm whitespace-nowrap">{d.entidad_responsable}</TableCell>
                  <TableCell className="text-sm">{d.accion}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>

      <Button type="button" variant="outline" size="sm" onClick={generar} className="w-fit">
        <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
        Regenerar recomendación
      </Button>
    </div>
  );
}

function ErrorPrescribe({ error }: { error: Error | null }) {
  const mensaje =
    error instanceof ApiError && error.status === 403
      ? "Tu rol no tiene permiso para generar recomendaciones."
      : (error?.message ?? "No se pudo generar la recomendación.");

  return (
    <Alert variant="destructive">
      <AlertTitle>No se pudo generar la recomendación</AlertTitle>
      <AlertDescription>{mensaje}</AlertDescription>
    </Alert>
  );
}
