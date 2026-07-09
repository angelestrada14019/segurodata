import { supabase } from "@/lib/supabase";
import type {
  AsignarCuadranteRequest,
  AsignarCuadranteResponse,
  ExplainResponse,
  GraphragRequest,
  GraphragResponse,
  PredictRequest,
  PredictResponse,
  PrescribeRequest,
  PrescribeResponse,
  WhoamiResponse,
} from "@/types/api";

const API_URL = import.meta.env.VITE_API_URL;

if (!API_URL) {
  throw new Error("Falta VITE_API_URL — revisa frontend/.env.local");
}

/**
 * Error tipado de la API — expone `.status` para que los hooks puedan
 * distinguir 401/403/404 sin parsear el mensaje.
 */
export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, message: string, body?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

async function obtenerBearerToken(): Promise<string | null> {
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}

async function request<TResponse>(
  path: string,
  options: RequestInit = {},
): Promise<TResponse> {
  const token = await obtenerBearerToken();

  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let body: unknown;
    try {
      body = await response.json();
    } catch {
      body = undefined;
    }
    const mensaje =
      (body as { detail?: string } | undefined)?.detail ??
      `Error ${response.status} al llamar ${path}`;
    throw new ApiError(response.status, mensaje, body);
  }

  return (await response.json()) as TResponse;
}

/**
 * Cliente tipado del backend FastAPI — un método por endpoint del contrato
 * `backend-segurodata`. Nunca inventar campos ni endpoints nuevos aquí sin
 * antes verificar contra la skill.
 */
export const apiClient = {
  predict: (body: PredictRequest) =>
    request<PredictResponse>("/predict", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  explain: (upzCod: string, anio: number, mes: number) =>
    request<ExplainResponse>(
      `/explain?upz_cod=${encodeURIComponent(upzCod)}&anio=${anio}&mes=${mes}`,
    ),

  prescribe: (body: PrescribeRequest) =>
    request<PrescribeResponse>("/prescribe", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  graphrag: (body: GraphragRequest) =>
    request<GraphragResponse>("/graphrag", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  whoami: () => request<WhoamiResponse>("/whoami"),

  asignarCuadrante: (userId: string, body: AsignarCuadranteRequest) =>
    request<AsignarCuadranteResponse>(
      `/admin/usuarios/${encodeURIComponent(userId)}/cuadrante`,
      {
        method: "PATCH",
        body: JSON.stringify(body),
      },
    ),
};
