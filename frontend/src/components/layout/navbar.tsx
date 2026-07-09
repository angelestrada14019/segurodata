import { NavLink } from "react-router-dom";
import { LogOut, ShieldAlert } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ModeToggle } from "@/components/layout/mode-toggle";
import { useAuth } from "@/hooks/use-auth";
import { supabase } from "@/lib/supabase";
import type { RolBackend } from "@/types/api";

interface NavItem {
  to: string;
  label: string;
  /** undefined = visible sin sesión también (ej. /diagnostico es pública). */
  rolesPermitidos?: RolBackend[];
}

/**
 * Matriz de visibilidad EXACTA (skill backend-segurodata + wiki_pages/Modulos.md):
 * CIUDADANO NO ve /prediccion (restricción de negocio real, no un olvido).
 * /diagnostico es la ÚNICA ruta pública — sin roles significa "sin sesión
 * también la ve", el resto requiere al menos estar logueado.
 */
const NAV_ITEMS: NavItem[] = [
  { to: "/diagnostico", label: "Diagnóstico" },
  {
    to: "/prediccion",
    label: "Predicción",
    rolesPermitidos: ["COMANDANTE_CAI", "ANALISTA_SDSCJ", "ADMIN"],
  },
  {
    to: "/prescriptivo",
    label: "Prescriptivo",
    rolesPermitidos: ["COMANDANTE_CAI", "ANALISTA_SDSCJ", "ADMIN"],
  },
  {
    to: "/chatbot",
    label: "Chatbot",
    rolesPermitidos: ["CIUDADANO", "COMANDANTE_CAI", "ANALISTA_SDSCJ", "ADMIN"],
  },
  {
    to: "/admin/usuarios",
    label: "Usuarios",
    rolesPermitidos: ["ADMIN"],
  },
];

export function Navbar() {
  const { session, rol } = useAuth();

  const itemsVisibles = NAV_ITEMS.filter((item) => {
    if (!item.rolesPermitidos) return true;
    if (!session) return false;
    if (!rol) return false;
    return item.rolesPermitidos.includes(rol);
  });

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-border bg-card/95 px-4 backdrop-blur-sm">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 font-mono-data text-sm font-semibold tracking-wide">
          <ShieldAlert className="h-4 w-4 text-primary" aria-hidden="true" />
          <span>SEGURODATA</span>
          <span className="text-muted-foreground">/ BOGOTÁ</span>
        </div>

        <nav aria-label="Navegación principal" className="flex items-center gap-1">
          {itemsVisibles.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  "rounded-sm px-3 py-1.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary/15 text-primary"
                    : "text-muted-foreground hover:bg-secondary hover:text-foreground",
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>

      <div className="flex items-center gap-2">
        {session ? (
          <>
            {rol && (
              <span className="hidden font-mono-data text-xs text-muted-foreground sm:inline">
                {rol}
              </span>
            )}
            <Button
              variant="ghost"
              size="icon"
              aria-label="Cerrar sesión"
              onClick={() => supabase.auth.signOut()}
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </>
        ) : (
          <Button asChild size="sm">
            <NavLink to="/login">Ingresar</NavLink>
          </Button>
        )}
        <ModeToggle />
      </div>
    </header>
  );
}
