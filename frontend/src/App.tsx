import { createBrowserRouter, Navigate, RouterProvider } from "react-router-dom";
import { RootLayout } from "@/routes/root";
import { ModuloDiagnosticoPage } from "@/routes/modulo1-diagnostico";
import { ModuloPrediccionPage } from "@/routes/modulo2-prediccion";
import { ModuloPrescriptivoPage } from "@/routes/modulo3-prescriptivo";
import { ModuloChatbotPage } from "@/routes/modulo4-chatbot";
import { AdminUsuariosPage } from "@/routes/admin-usuarios";
import { LoginPage } from "@/routes/login";
import { CuadrantePendientePage } from "@/routes/cuadrante-pendiente";
import { NoAutorizadoPage } from "@/routes/no-autorizado";
import { ProtectedRoute } from "@/components/layout/protected-route";

/**
 * Router raíz — data router (createBrowserRouter), requerido para que
 * `<Route lazy={...}>` funcione en el futuro (React 19, ver skill
 * react-patterns). `/diagnostico` es la ÚNICA ruta sin ProtectedRoute
 * (mapa público de solo lectura). Matriz de roles: skill backend-segurodata
 * + wiki_pages/Modulos.md.
 */
const router = createBrowserRouter([
  {
    path: "/",
    element: <RootLayout />,
    children: [
      { index: true, element: <Navigate to="/diagnostico" replace /> },
      { path: "diagnostico", element: <ModuloDiagnosticoPage /> },
      {
        path: "prediccion",
        element: (
          <ProtectedRoute
            rolesPermitidos={["COMANDANTE_CAI", "ANALISTA_SDSCJ", "ADMIN"]}
          >
            <ModuloPrediccionPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "prescriptivo",
        element: (
          <ProtectedRoute
            rolesPermitidos={["COMANDANTE_CAI", "ANALISTA_SDSCJ", "ADMIN"]}
          >
            <ModuloPrescriptivoPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "chatbot",
        element: (
          <ProtectedRoute
            rolesPermitidos={[
              "CIUDADANO",
              "COMANDANTE_CAI",
              "ANALISTA_SDSCJ",
              "ADMIN",
            ]}
          >
            <ModuloChatbotPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "admin/usuarios",
        element: (
          <ProtectedRoute rolesPermitidos={["ADMIN"]}>
            <AdminUsuariosPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "cuadrante-pendiente",
        element: (
          <ProtectedRoute rolesPermitidos={["COMANDANTE_CAI"]}>
            <CuadrantePendientePage />
          </ProtectedRoute>
        ),
      },
      { path: "no-autorizado", element: <NoAutorizadoPage /> },
    ],
  },
  { path: "/login", element: <LoginPage /> },
]);

function App() {
  return <RouterProvider router={router} />;
}

export default App;
