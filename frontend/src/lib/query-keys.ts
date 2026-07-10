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
  /**
   * Período (anio, mes) más reciente resuelto vía RPC `periodo_mas_reciente`
   * (ver `lib/periodo-predicciones.ts`). Solo lo consume `use-diagnostico-upz.ts`
   * — `use-upz-geometrias.ts`/`use-localidades-geometrias.ts` resuelven el
   * período DENTRO de su propio queryFn (no como query separada) porque ahí
   * solo alimenta una única llamada; aquí alimenta dos (`usePredict` +
   * `useExplain`), así que se cachea aparte para no resolverlo dos veces.
   */
  periodoVigente: ["periodo-vigente"] as const,
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
  /**
   * Lista liviana `{cuadrante_id, nom_cai}` para el `<Select>` del Panel
   * Admin (`hooks/use-cuadrantes.ts`). Deliberadamente DISTINTA de
   * `cuadrantesGeometrias.all` (RPC `cuadrantes_geojson`, geometría completa
   * para la capa del mapa) — mismo nombre de key para ambas causaría que
   * TanStack Query devolviera una forma de dato por la otra.
   */
  cuadrantesOpciones: {
    all: ["cuadrantes-opciones"] as const,
  },
} as const;
