/**
 * Factory centralizada de query keys — evita strings mágicos repetidos y
 * facilita invalidación granular (`queryClient.invalidateQueries({ queryKey: queryKeys.upzGeometrias.all })`).
 */
export const queryKeys = {
  whoami: ["whoami"] as const,

  upzGeometrias: {
    all: ["upz-geometrias"] as const,
    byPeriodo: (anio?: number, mes?: number) =>
      ["upz-geometrias", { anio, mes }] as const,
  },
  localidadesGeometrias: {
    all: ["localidades-geometrias"] as const,
    byPeriodo: (anio?: number, mes?: number) =>
      ["localidades-geometrias", { anio, mes }] as const,
  },
  cuadrantesGeometrias: {
    all: ["cuadrantes-geometrias"] as const,
  },

  // Sprint 2
  predict: (upzCod: string, anio: number, mes: number) =>
    ["predict", upzCod, anio, mes] as const,
  explain: (upzCod: string, anio: number, mes: number) =>
    ["explain", upzCod, anio, mes] as const,
  prediccionesMes: (anio: number, mes: number) =>
    ["predicciones-mes", anio, mes] as const,
  changePoints: {
    all: ["change-points"] as const,
  },
  silverRealtime: (upzCod: string) => ["silver-realtime", upzCod] as const,

  // Sprint 3
  prescribe: (upzCod: string) => ["prescribe", upzCod] as const,
  graphrag: (pregunta: string, upzContexto?: string) =>
    ["graphrag", pregunta, upzContexto] as const,
  adminUsuarios: {
    all: ["admin-usuarios"] as const,
  },
} as const;
