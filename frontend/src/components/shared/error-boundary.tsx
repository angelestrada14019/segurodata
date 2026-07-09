import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ErrorBoundaryProps {
  children: ReactNode;
  /** Contenido de fallback a mostrar. Si se omite, usa el fallback por defecto. */
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * Error boundary genérico — envuelve secciones que dependen de datos externos
 * (mapa, modal UPZ, chatbot) para que un fallo no tumbe todo el dashboard.
 * Componente de clase: es el único mecanismo soportado por React para
 * capturar errores de render de sus hijos (no existe hook equivalente).
 */
export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary capturó un error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div
          role="alert"
          className="flex flex-col items-center justify-center gap-3 rounded-md border border-destructive/40 bg-destructive/10 p-8 text-center"
        >
          <AlertTriangle className="h-8 w-8 text-destructive" aria-hidden="true" />
          <p className="font-medium text-foreground">
            Ocurrió un error al cargar esta sección
          </p>
          <p className="max-w-md text-sm text-muted-foreground">
            {this.state.error?.message ?? "Error desconocido"}
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => this.setState({ hasError: false, error: null })}
          >
            Reintentar
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}
