import { etiquetaFeature } from "@/lib/features-modelo";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { DiagnosticoPrescriptivo } from "@/types/api";

interface TablaOntologicaProps {
  diagnosticos: DiagnosticoPrescriptivo[];
}

/**
 * Tabla "Diagnóstico por variable" — la tabla ontológica del Módulo 3: por
 * cada causa dominante (feature SHAP) mapea diagnóstico → tipo de
 * intervención → entidad responsable → acción concreta. Es el diferenciador
 * clave del proyecto (ver CLAUDE.md raíz): no solo predice, dice a quién
 * avisar y por qué.
 *
 * Extraída de `tab-sugerencia.tsx` (modal UPZ) para compartirla con
 * `routes/modulo3-prescriptivo.tsx` (vista standalone) — ambos consumen la
 * misma forma exacta de `PrescribeResponse.diagnosticos` (POST /prescribe,
 * skill backend-segurodata). Nunca reintroducir este JSX inline en otro lugar.
 */
export function TablaOntologica({ diagnosticos }: TablaOntologicaProps) {
  return (
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
            {diagnosticos.map((d) => (
              <TableRow key={d.feature}>
                <TableCell className="font-mono-data text-xs whitespace-nowrap">
                  {etiquetaFeature(d.feature)}
                </TableCell>
                <TableCell className="text-sm">{d.diagnostico}</TableCell>
                <TableCell className="text-sm whitespace-nowrap">
                  {d.tipo_intervencion}
                </TableCell>
                <TableCell className="text-sm whitespace-nowrap">
                  {d.entidad_responsable}
                </TableCell>
                <TableCell className="text-sm">{d.accion}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
