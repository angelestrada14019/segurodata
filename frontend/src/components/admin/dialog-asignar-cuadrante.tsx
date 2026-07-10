import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { useCuadrantes } from "@/hooks/use-cuadrantes";
import { useAdminAsignarCuadrante } from "@/hooks/use-admin-asignar-cuadrante";
import { ApiError } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { UserProfileRow } from "@/types/supabase";

interface DialogAsignarCuadranteProps {
  usuario: UserProfileRow;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/**
 * Dialog de asignación/reasignación de cuadrante — único punto de escritura
 * del Panel Admin. Confirma con `useAdminAsignarCuadrante()` (PATCH
 * /admin/usuarios/{id}/cuadrante, rol ADMIN — skill backend-segurodata). Su
 * `onSuccess` (definido en el hook, no aquí) invalida
 * `queryKeys.adminUsuarios.all`, así que `routes/admin-usuarios.tsx` se
 * refresca solo tras confirmar — esta pieza nunca actualiza la fila a mano.
 *
 * `usuario` siempre llega no-nulo: `admin-usuarios.tsx` solo monta este
 * componente cuando hay una fila seleccionada (mismo patrón "sticky" que
 * `components/mapa/mapa-riesgo.tsx` usa para `<ModalUpz>` — conserva el
 * último usuario elegido en pantalla mientras Radix anima el cierre, en vez
 * de vaciar el contenido a mitad de la animación).
 */
export function DialogAsignarCuadrante({
  usuario,
  open,
  onOpenChange,
}: DialogAsignarCuadranteProps) {
  const [cuadranteId, setCuadranteId] = useState<string | undefined>(
    usuario.cuadrante_asignado ?? undefined,
  );

  const cuadrantesQuery = useCuadrantes();
  const mutation = useAdminAsignarCuadrante();

  // Patrón "ref con el valor más reciente" (ver modal-upz.tsx /
  // modulo3-prescriptivo.tsx): `mutation` es un objeto nuevo en cada render
  // (useMutation), así que el efecto de abajo solo debe reaccionar a un
  // cambio real de usuario — nunca a la identidad de ese objeto.
  const mutationRef = useRef(mutation);
  mutationRef.current = mutation;

  useEffect(() => {
    setCuadranteId(usuario.cuadrante_asignado ?? undefined);
    mutationRef.current.reset();
  }, [usuario.user_id, usuario.cuadrante_asignado]);

  const yaAsignado = !!usuario.cuadrante_asignado;

  function confirmar() {
    if (!cuadranteId) return;
    mutation.mutate(
      { userId: usuario.user_id, body: { cuadrante_id: cuadranteId } },
      {
        onSuccess: () => {
          toast.success("Cuadrante asignado", {
            description: `${usuario.email} → cuadrante ${cuadranteId}`,
          });
          onOpenChange(false);
        },
        onError: (error) => {
          toast.error("No se pudo asignar el cuadrante", {
            description:
              error instanceof ApiError
                ? error.message
                : "Intenta de nuevo en unos segundos.",
          });
        },
      },
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="font-mono-data tracking-wide">
            {yaAsignado ? "Reasignar cuadrante" : "Asignar cuadrante"}
          </DialogTitle>
          <DialogDescription>
            {usuario.email}
            {yaAsignado && (
              <>
                {" "}
                — cuadrante actual:{" "}
                <span className="font-mono-data">{usuario.cuadrante_asignado}</span>
              </>
            )}
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-1.5">
          <Label
            htmlFor="select-cuadrante"
            className="text-xs tracking-wide text-muted-foreground uppercase"
          >
            Cuadrante
          </Label>
          <Select
            value={cuadranteId}
            onValueChange={setCuadranteId}
            disabled={
              cuadrantesQuery.isLoading || cuadrantesQuery.isError || mutation.isPending
            }
          >
            <SelectTrigger id="select-cuadrante">
              <SelectValue
                placeholder={
                  cuadrantesQuery.isLoading
                    ? "Cargando cuadrantes…"
                    : cuadrantesQuery.isError
                      ? "No se pudo cargar la lista"
                      : "Selecciona un cuadrante"
                }
              />
            </SelectTrigger>
            <SelectContent>
              {cuadrantesQuery.data?.map((c) => (
                <SelectItem key={c.cuadrante_id} value={c.cuadrante_id}>
                  <span className="font-mono-data mr-2 text-xs text-muted-foreground">
                    {c.cuadrante_id}
                  </span>
                  {c.nom_cai ?? "Sin nombre"}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {cuadrantesQuery.isError && (
            <p role="alert" className="text-xs text-destructive">
              No se pudo cargar la lista de cuadrantes — intenta recargar la página.
            </p>
          )}
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={mutation.isPending}
          >
            Cancelar
          </Button>
          <Button
            type="button"
            onClick={confirmar}
            disabled={!cuadranteId || mutation.isPending}
          >
            {mutation.isPending ? "Asignando…" : "Confirmar"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
