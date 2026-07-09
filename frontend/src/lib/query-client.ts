import { QueryClient } from "@tanstack/react-query";

/**
 * QueryClient único de la app. staleTime 60s por defecto — los datos de
 * predicción/geometría cambian a lo sumo mensualmente, no hace falta
 * refetch agresivo. Queries específicas (ej. geometrías sin anio/mes)
 * pueden subir staleTime a Infinity en su propio hook.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});
