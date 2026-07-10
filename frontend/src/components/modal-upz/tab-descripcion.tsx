import { MapPin, ShieldAlert } from "lucide-react";
import { BadgeNivelRiesgo } from "@/components/shared/badge-nivel-riesgo";
import { PanelSkeleton } from "@/components/shared/loading-states";
import type { UpzFeature } from "@/types/deck";

interface TabDescripcionProps {
  upzCod: string;
  upzFeature: UpzFeature | undefined;
  cargando: boolean;
}

/**
 * Ficha de identidad de la UPZ — nombre, localidad y nivel de riesgo
 * vigente. `upzFeature` viene del cache compartido de `useUpzGeometrias()`
 * (mismo query key que ya usa el mapa): si el usuario abrió el modal desde
 * un click en el mapa, esta data ya está en memoria, sin round-trip nuevo.
 */
export function TabDescripcion({ upzCod, upzFeature, cargando }: TabDescripcionProps) {
  if (!upzFeature && cargando) {
    return <PanelSkeleton lineas={4} />;
  }

  if (!upzFeature) {
    return (
      <div
        role="status"
        className="flex flex-col items-center gap-2 rounded-md border border-border bg-card p-8 text-center"
      >
        <MapPin className="h-6 w-6 text-muted-foreground" aria-hidden="true" />
        <p className="text-sm text-muted-foreground">
          No se encontró información geográfica para la UPZ{" "}
          <span className="font-mono-data">{upzCod}</span>.
        </p>
      </div>
    );
  }

  const { upz_nombre, cod_localidad, nom_localidad, nivel_riesgo } =
    upzFeature.properties;

  const localidadTexto = nom_localidad
    ? `${nom_localidad} (${cod_localidad})`
    : "No disponible";

  const campos: Array<{ etiqueta: string; valor: string }> = [
    { etiqueta: "Código UPZ", valor: upzCod },
    { etiqueta: "Localidad", valor: localidadTexto },
  ];

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start justify-between gap-4 rounded-md border border-border bg-card p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-sm border border-border bg-secondary">
            <ShieldAlert className="h-5 w-5 text-primary" aria-hidden="true" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-foreground">{upz_nombre}</h3>
            <p className="font-mono-data text-xs text-muted-foreground">
              UPZ {upzCod}
              {nom_localidad ? ` · ${nom_localidad}` : ""}
            </p>
          </div>
        </div>
        <BadgeNivelRiesgo nivelRiesgo={nivel_riesgo} />
      </div>

      <dl className="grid grid-cols-1 gap-px overflow-hidden rounded-md border border-border bg-border sm:grid-cols-2">
        {campos.map((campo) => (
          <div key={campo.etiqueta} className="bg-card p-3">
            <dt className="text-xs text-muted-foreground uppercase tracking-wide">
              {campo.etiqueta}
            </dt>
            <dd className="mt-1 font-mono-data text-sm text-foreground">{campo.valor}</dd>
          </div>
        ))}
      </dl>

      <p className="text-sm text-muted-foreground">
        El nivel de riesgo mostrado corresponde al último período con datos
        disponibles. El detalle de probabilidades por banda y las variables
        que más influyen en la predicción están en la pestaña{" "}
        <span className="font-medium text-foreground">Predicción</span>.
      </p>
    </div>
  );
}
