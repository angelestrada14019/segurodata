import { useMemo, useState } from "react";
import { Check, ChevronDown } from "lucide-react";
import { useUpzGeometrias } from "@/hooks/use-upz-geometrias";
import { cn } from "@/lib/utils";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";

interface SelectorUpzProps {
  value: string | undefined;
  onValueChange: (upzCod: string) => void;
  disabled?: boolean;
}

/**
 * Selector standalone de UPZ para el Módulo 3 — Prescriptivo. Combobox
 * buscable (Popover + Command/cmdk), no un `<Select>` simple: con 112 UPZs,
 * el `<Select>` de Radix no dejaba hacer scroll más allá de las primeras
 * filas (su `Viewport` en modo "popper" fija la altura a la del trigger,
 * `h-[var(--radix-select-trigger-height)]` en `components/ui/select.tsx`) y
 * de todas formas un `<select>` no soporta filtrar. `CommandList` resuelve
 * el scroll con `max-h-72 overflow-y-auto` propio, sin depender de esa
 * variable, y `CommandInput` da el filtro en el mismo control.
 *
 * El texto de búsqueda de cada `CommandItem` concatena código + nombre +
 * localidad para que el filtro de cmdk funcione con cualquiera de los tres
 * (ej. "023", "casa blanca" o "suba" encuentran la misma fila) — pero la
 * selección real (`onValueChange`) siempre usa `opcion.upzCod` por closure,
 * nunca parseando ese string de búsqueda.
 *
 * Puebla la lista desde `useUpzGeometrias()` (mismo query key que ya usa el
 * mapa y el modal UPZ; si esas vistas ya se visitaron, esta data llega sin
 * round-trip nuevo).
 */
export function SelectorUpz({ value, onValueChange, disabled }: SelectorUpzProps) {
  const { data, isLoading, isError } = useUpzGeometrias();
  const [abierto, setAbierto] = useState(false);

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

  const seleccionada = opciones.find((o) => o.upzCod === value);

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
      <Popover open={abierto} onOpenChange={setAbierto}>
        <PopoverTrigger asChild>
          <Button
            id="selector-upz"
            type="button"
            variant="outline"
            role="combobox"
            aria-expanded={abierto}
            disabled={disabled || isLoading || isError}
            className="w-full justify-between font-normal sm:w-96"
          >
            <span className={cn("truncate", !seleccionada && "text-muted-foreground")}>
              {seleccionada ? (
                <>
                  <span className="font-mono-data mr-2 text-xs text-muted-foreground">
                    {seleccionada.upzCod}
                  </span>
                  {seleccionada.upzNombre}
                  {seleccionada.nomLocalidad && (
                    <span className="ml-2 text-xs text-muted-foreground">
                      ({seleccionada.nomLocalidad})
                    </span>
                  )}
                </>
              ) : (
                placeholder
              )}
            </span>
            <ChevronDown className="h-4 w-4 shrink-0 opacity-50" aria-hidden="true" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[--radix-popover-trigger-width] p-0" align="start">
          <Command>
            <CommandInput placeholder="Buscar por código, nombre o localidad…" />
            <CommandList>
              <CommandEmpty>Ninguna UPZ coincide.</CommandEmpty>
              <CommandGroup>
                {opciones.map((opcion) => (
                  <CommandItem
                    key={opcion.upzCod}
                    value={`${opcion.upzCod} ${opcion.upzNombre} ${opcion.nomLocalidad ?? ""}`}
                    onSelect={() => {
                      onValueChange(opcion.upzCod);
                      setAbierto(false);
                    }}
                  >
                    <Check
                      className={cn(
                        "mr-2 h-4 w-4 shrink-0",
                        opcion.upzCod === value ? "opacity-100" : "opacity-0",
                      )}
                      aria-hidden="true"
                    />
                    <span className="font-mono-data mr-2 text-xs text-muted-foreground">
                      {opcion.upzCod}
                    </span>
                    <span className="truncate">{opcion.upzNombre}</span>
                    {opcion.nomLocalidad && (
                      <span className="ml-2 shrink-0 text-xs text-muted-foreground">
                        ({opcion.nomLocalidad})
                      </span>
                    )}
                  </CommandItem>
                ))}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
      {isError && (
        <p role="alert" className="text-xs text-destructive">
          No se pudo cargar la lista de UPZs — intenta recargar la página.
        </p>
      )}
    </div>
  );
}
