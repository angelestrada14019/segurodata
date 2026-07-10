import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/lib/supabase";
import { queryKeys } from "@/lib/query-keys";
import { obtenerPeriodoMasReciente } from "@/lib/periodo-predicciones";

export interface Periodo {
  anio: number;
  mes: number;
}

export interface RangoPeriodos {
  /** Período más antiguo con predicciones disponible. */
  desde: Periodo;
  /** Período más reciente con predicciones disponible (== `usePeriodoVigente`). */
  hasta: Periodo;
}

/**
 * Ventana de respaldo (en meses) para cuando RLS bloquea la consulta directa
 * a `predicciones` — la política `predicciones_por_rol` (migración 0006) es
 * `FOR SELECT TO authenticated`, así que un visitante `anon` en /diagnostico
 * (mapa público, ver `routes/modulo1-diagnostico.tsx`) recibe 0 filas, NO un
 * error (mismo comportamiento ya documentado en `lib/periodo-predicciones.ts`).
 * No existe una RPC `SECURITY DEFINER` que exponga el rango completo a anon
 * (solo `periodo_mas_reciente`, migración 0013) — en vez de bloquear el
 * slider para el visitante público, se degrada a una ventana relativa al
 * período vigente. Las sesiones autenticadas (COMANDANTE_CAI/ANALISTA_SDSCJ/
 * ADMIN/CIUDADANO logueado) sí ven el rango real de la tabla.
 */
const VENTANA_RESPALDO_MESES = 11;

/**
 * Rango (desde, hasta) de períodos con predicciones disponibles — alimenta
 * `slider-temporal.tsx`. Dos consultas `limit(1)` (una ASC, una DESC) en vez
 * de traer todas las filas: solo hacen falta los dos extremos.
 */
export function useRangoPeriodos() {
  return useQuery({
    queryKey: queryKeys.rangoPeriodos,
    queryFn: async (): Promise<RangoPeriodos | null> => {
      const [masAntiguo, masReciente] = await Promise.all([
        supabase
          .from("predicciones")
          .select("anio, mes")
          .order("anio", { ascending: true })
          .order("mes", { ascending: true })
          .limit(1),
        supabase
          .from("predicciones")
          .select("anio, mes")
          .order("anio", { ascending: false })
          .order("mes", { ascending: false })
          .limit(1),
      ]);

      const filaAntigua = masAntiguo.data?.[0];
      const filaReciente = masReciente.data?.[0];

      if (!masAntiguo.error && !masReciente.error && filaAntigua && filaReciente) {
        return {
          desde: { anio: filaAntigua.anio, mes: filaAntigua.mes },
          hasta: { anio: filaReciente.anio, mes: filaReciente.mes },
        };
      }

      // RLS bloqueó la consulta (anon) o la tabla está vacía para este rol —
      // degradación a ventana relativa al período vigente (RPC anon-safe).
      const vigente = await obtenerPeriodoMasReciente();
      if (!vigente) return null;
      return { desde: restarMeses(vigente, VENTANA_RESPALDO_MESES), hasta: vigente };
    },
    staleTime: 5 * 60_000,
  });
}

function restarMeses(periodo: Periodo, n: number): Periodo {
  const ordinal = periodo.anio * 12 + (periodo.mes - 1) - n;
  return { anio: Math.floor(ordinal / 12), mes: (ordinal % 12) + 1 };
}
