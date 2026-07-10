import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/lib/supabase";
import { queryKeys } from "@/lib/query-keys";
import type { CuadranteOpcionRow } from "@/types/supabase";

/**
 * Lista liviana de cuadrantes (`cuadrante_id` + `nom_cai`) para poblar el
 * `<Select>` de asignación de cuadrante del Panel Admin. A propósito NO
 * reusa la RPC `cuadrantes_geojson` (migración 0012) — esa trae la
 * geometría completa de los 599 cuadrantes, peso innecesario para un
 * dropdown. Lee `cuadrantes_geom` directo proyectando solo las dos columnas
 * que hacen falta (schema real en
 * `supabase/migrations/20260610_0003_geo_tables.sql`).
 */
export function useCuadrantes() {
  return useQuery({
    queryKey: queryKeys.cuadrantesOpciones.all,
    queryFn: async (): Promise<CuadranteOpcionRow[]> => {
      const { data, error } = await supabase
        .from("cuadrantes_geom")
        .select("cuadrante_id, nom_cai")
        .order("cuadrante_id", { ascending: true });
      if (error) throw error;
      return data;
    },
    staleTime: 5 * 60_000,
  });
}
