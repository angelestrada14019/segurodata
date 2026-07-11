import ReactMarkdown from "react-markdown";
import remarkBreaks from "remark-breaks";
import { cn } from "@/lib/utils";

interface TextoMarkdownProps {
  children: string;
  className?: string;
}

/**
 * Renderiza texto generado por LLM (recomendación prescriptiva, respuestas
 * del chatbot) — ambos vienen de OpenRouter y suelen incluir **negrita**,
 * listas, etc. aunque el prompt no lo pida explícitamente; sin parsear se
 * veían los asteriscos crudos en pantalla. `remark-breaks` respeta saltos
 * de línea simples como <br> (el LLM no siempre separa párrafos con línea
 * en blanco) — mismo comportamiento visual que el `whitespace-pre-wrap`
 * que reemplaza este componente.
 *
 * Sin HTML crudo (`ReactMarkdown` no lo renderiza por defecto) — solo
 * markdown → elementos React, sin superficie de XSS nueva.
 */
export function TextoMarkdown({ children, className }: TextoMarkdownProps) {
  return (
    <div className={cn("text-sm leading-relaxed text-foreground", className)}>
      <ReactMarkdown
        remarkPlugins={[remarkBreaks]}
        components={{
          p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
          strong: ({ children }) => (
            <strong className="font-semibold text-foreground">{children}</strong>
          ),
          em: ({ children }) => <em className="italic">{children}</em>,
          ul: ({ children }) => (
            <ul className="mb-2 ml-4 list-disc space-y-1 last:mb-0">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="mb-2 ml-4 list-decimal space-y-1 last:mb-0">{children}</ol>
          ),
          li: ({ children }) => <li>{children}</li>,
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary underline-offset-2 hover:underline"
            >
              {children}
            </a>
          ),
          code: ({ children }) => (
            <code className="rounded bg-muted px-1 py-0.5 font-mono-data text-xs">
              {children}
            </code>
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
