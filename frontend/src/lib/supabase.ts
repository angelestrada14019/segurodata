import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    "Faltan VITE_SUPABASE_URL o VITE_SUPABASE_ANON_KEY — revisa frontend/.env.local",
  );
}

/**
 * Cliente Supabase ÚNICO (singleton) para todo el frontend.
 *
 * Usa la clave anon/publishable — RLS filtra por rol y `cuadrante_asignado`
 * (ver migraciones 0006/0012 y skill `supabase-segurodata`). NUNCA importar
 * la service key aquí: bypasea RLS y expondría datos de otros cuadrantes.
 */
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
});
