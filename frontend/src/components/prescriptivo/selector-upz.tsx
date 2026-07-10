import { useMemo } from "react";
import { useUpzGeometrias } from "@/hooks/use-upz-geometrias";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface SelectorUpzProps {
  value: string | undefined;
  onValueChange: (upzCod: string) => void;
  disabled?: boolean;
}

/**
 * Selector standalone de UPZ para el Módulo 3 — Prescriptivo. Puebla la
 * lista desde `useUpzGeometrias()` (mismo query key que ya usa el mapa y el
 * modal UPZ; si esas vistas ya se visitaron, esta data llega sin round-trip
 * nuevo). Permite entrar a `/prescriptivo` y elegir cualquier UPZ sin
 * depender de haber hecho click antes en el mapa.
 */
export function SelectorUpz({ value, onValueChange, disabled }: SelectorUpzProps) {
  const { data, isLoading, isError } = useUpzGeometrias();

  const opciones = useMemo(() => {
    if (!data) return [];
    return data.features
      .map((f) => ({
        upzCod: f.properties.upz_cod,
        upzNombre: f.properties.upz_nombre,
        nomLocalidad: f.properties.nom_localidad,
      }))
      .sort((a, b) => a.upzNombre.localeCompare(b.upzNombre, "es"));
  }, [data]);

  const placeholder = isLoading
    ? "Cargando UPZs…"
    : isError
      ? "No se pudo cargar la lista de UPZs"
      : "Selecciona una UPZ";

  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor="selector-upz" className="text-xs tracking-wide text-muted-foreground uppercase">
        UPZ
      </Label>
      <Select
        value={value}
        onValueChange={onValueChange}
        disabled={disabled || isLoading || isError}
      >
        <SelectTrigger id="selector-upz" className="w-full sm:w-96">
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>
          {opciones.map((opcion) => (
            <SelectItem key={opcion.upzCod} value={opcion.upzCod}>
              <span className="font-mono-data mr-2 text-xs text-muted-foreground">
                {opcion.upzCod}
              </span>
              {opcion.upzNombre}
              {opcion.nomLocalidad && (
                <span className="ml-2 text-xs text-muted-foreground">
                  ({opcion.nomLocalidad})
                </span>
              )}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {isError && (
        <p role="alert" className="text-xs text-destructive">
          No se pudo cargar la lista de UPZs — intenta recargar la página.
        </p>
      )}
    </div>
  );
}
