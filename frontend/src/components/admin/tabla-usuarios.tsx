import { CircleCheck, CircleDashed, MapPinned } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FilaTablaSkeleton } from "@/components/shared/loading-states";
import type { UserProfileRow } from "@/types/supabase";

const COLUMNAS = 6;
/** Filas skeleton mientras carga — número arbitrario, solo estético. */
const FILAS_SKELETON = 6;

interface TablaUsuariosProps {
  usuarios: UserProfileRow[] | undefined;
  isLoading: boolean;
  onAsignarCuadrante: (usuario: UserProfileRow) => void;
}

/**
 * Tabla del Panel Admin (`/admin/usuarios`) — una fila por perfil
 * (`user_profiles`). Solo las filas COMANDANTE_CAI muestran la acción
 * "Asignar cuadrante": es el único rol cuyas predicciones la RLS filtra por
 * `cuadrante_asignado` (`supabase/migrations/20260610_0008_advisor_fixes.sql`)
 * — el resto de roles no usa ese campo, así que la acción no aplica.
 *
 * El encabezado (`<TableHeader>`) se mantiene montado durante la carga —
 * solo el cuerpo alterna entre `FilaTablaSkeleton` (loading), filas reales
 * y el estado vacío, para no generar layout shift (ver comentario en
 * `components/shared/loading-states.tsx`).
 */
export function TablaUsuarios({
  usuarios,
  isLoading,
  onAsignarCuadrante,
}: TablaUsuariosProps) {
  return (
    <div className="rounded-md border border-border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Correo</TableHead>
            <TableHead>Rol</TableHead>
            <TableHead>Cuadrante asignado</TableHead>
            <TableHead>Estado</TableHead>
            <TableHead>Creado</TableHead>
            <TableHead className="text-right">Acciones</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading &&
            Array.from({ length: FILAS_SKELETON }).map((_, i) => (
              <FilaTablaSkeleton key={i} columnas={COLUMNAS} />
            ))}

          {!isLoading && usuarios?.length === 0 && (
            <TableRow>
              <TableCell
                colSpan={COLUMNAS}
                className="p-8 text-center text-sm text-muted-foreground"
              >
                Todavía no hay usuarios registrados.
              </TableCell>
            </TableRow>
          )}

          {!isLoading &&
            usuarios?.map((usuario) => (
              <FilaUsuario
                key={usuario.user_id}
                usuario={usuario}
                onAsignarCuadrante={onAsignarCuadrante}
              />
            ))}
        </TableBody>
      </Table>
    </div>
  );
}

interface FilaUsuarioProps {
  usuario: UserProfileRow;
  onAsignarCuadrante: (usuario: UserProfileRow) => void;
}

function FilaUsuario({ usuario, onAsignarCuadrante }: FilaUsuarioProps) {
  return (
    <TableRow>
      <TableCell className="text-sm text-foreground">{usuario.email}</TableCell>
      <TableCell>
        <Badge variant="outline" className="font-mono-data text-[10px] uppercase">
          {usuario.rol}
        </Badge>
      </TableCell>
      <TableCell className="font-mono-data text-xs text-muted-foreground">
        {usuario.cuadrante_asignado ?? "—"}
      </TableCell>
      <TableCell>
        <EstadoAprobado aprobado={usuario.aprobado} />
      </TableCell>
      <TableCell className="text-xs text-muted-foreground">
        {formatearFechaCreacion(usuario.created_at)}
      </TableCell>
      <TableCell className="text-right">
        {usuario.rol === "COMANDANTE_CAI" ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => onAsignarCuadrante(usuario)}
            aria-label={`${usuario.cuadrante_asignado ? "Reasignar" : "Asignar"} cuadrante para ${usuario.email}`}
          >
            <MapPinned className="h-3.5 w-3.5" aria-hidden="true" />
            {usuario.cuadrante_asignado ? "Reasignar" : "Asignar cuadrante"}
          </Button>
        ) : (
          <span className="text-xs text-muted-foreground">—</span>
        )}
      </TableCell>
    </TableRow>
  );
}

function EstadoAprobado({ aprobado }: { aprobado: boolean }) {
  if (aprobado) {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs text-success">
        <CircleCheck className="h-3.5 w-3.5" aria-hidden="true" />
        Aprobado
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-warning">
      <CircleDashed className="h-3.5 w-3.5" aria-hidden="true" />
      Pendiente
    </span>
  );
}

function formatearFechaCreacion(iso: string): string {
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) return iso;
  return new Intl.DateTimeFormat("es-CO", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(parsed);
}
