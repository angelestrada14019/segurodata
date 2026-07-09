import { use } from "react";
import { AuthContext } from "@/context/auth-provider";

/**
 * Hook público de auth — consume `AuthContext`. Usar `use()` (React 19) en
 * vez de `useContext` para poder invocarlo dentro de condicionales si hiciera
 * falta en el futuro.
 */
export function useAuth() {
  const context = use(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth debe usarse dentro de <AuthProvider>");
  }
  return context;
}
