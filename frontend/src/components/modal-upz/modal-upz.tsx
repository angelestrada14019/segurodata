import { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useDiagnosticoUpz } from "@/hooks/use-diagnostico-upz";
import { useUpzGeometrias } from "@/hooks/use-upz-geometrias";
import { useGraphrag } from "@/hooks/use-graphrag";
import { TabDescripcion } from "@/components/modal-upz/tab-descripcion";
import { TabPrediccion } from "@/components/modal-upz/tab-prediccion";
import { TabSugerencia } from "@/components/modal-upz/tab-sugerencia";
import { TabFuentes } from "@/components/modal-upz/tab-fuentes";
import { TabChatbot } from "@/components/modal-upz/tab-chatbot";
import type { MensajeChat } from "@/components/modal-upz/tipos";
import type { GraphragResponse } from "@/types/api";

interface ModalUpzProps {
  upzCod: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const PESTANAS = [
  { valor: "descripcion", etiqueta: "Descripción" },
  { valor: "prediccion", etiqueta: "Predicción" },
  { valor: "sugerencia", etiqueta: "Sugerencia" },
  { valor: "fuentes", etiqueta: "Fuentes" },
  { valor: "chatbot", etiqueta: "Chatbot" },
] as const;

/**
 * Modal de 5 pestañas por UPZ — pieza central de Sprint 2, prerequisito de
 * los Módulos 2 y 3. Dueño de todo el estado que necesita sobrevivir a
 * cambios de pestaña (Radix Tabs desmonta el contenido de la pestaña
 * inactiva — ver `@radix-ui/react-tabs`, `Presence present={forceMount ||
 * isSelected}` — así que nada que deba persistir entre pestañas puede vivir
 * como estado local de un tab hijo):
 *
 * - `useDiagnosticoUpz` (predict + explain del período vigente) — lo
 *   consume Predicción y alimenta a Sugerencia vía `shap_top3`.
 * - `useUpzGeometrias()` — mismo query key que ya usa el mapa (Sprint 1),
 *   así que si el modal se abrió desde un click en el mapa esta data ya
 *   está en cache, sin round-trip nuevo. Alimenta a Descripción.
 * - `useGraphrag()` — ÚNICA instancia, compartida entre Fuentes (lectura)
 *   y Chatbot (dispara `.mutate`).
 * - `historialChat` — transcripción acumulada del chatbot.
 *
 * Se pasa todo a los 5 hijos por props: son 5 hermanos directos, un Context
 * aquí sería indirección sin beneficio (ver skill react-patterns).
 */
export function ModalUpz({ upzCod, open, onOpenChange }: ModalUpzProps) {
  const [tabActiva, setTabActiva] = useState<string>("descripcion");
  const [historialChat, setHistorialChat] = useState<MensajeChat[]>([]);

  const graphragMutation = useGraphrag();

  // Nueva UPZ → se reinicia la sesión del modal (pestaña activa, historial
  // de chat, mutación graphrag). `graphragMutation` es un objeto nuevo en
  // cada render (useMutation) — solo nos interesa reaccionar a cambios de
  // `upzCod`, no a la identidad del objeto mutation.
  useEffect(() => {
    setTabActiva("descripcion");
    setHistorialChat([]);
    graphragMutation.reset();
    // Deps intencional: solo [upzCod]. `graphragMutation` es un objeto nuevo
    // en cada render (useMutation) — incluirlo dispararía este efecto en
    // renders donde upzCod no cambió.
  }, [upzCod]);

  const {
    prediccion,
    explicacion,
    isLoading: prediccionCargando,
    error: prediccionError,
  } = useDiagnosticoUpz(upzCod, open);

  const upzGeometriasQuery = useUpzGeometrias();
  const upzFeature = upzGeometriasQuery.data?.features.find(
    (f) => f.properties.upz_cod === upzCod,
  );

  function handleNuevaRespuesta(pregunta: string, respuesta: GraphragResponse) {
    setHistorialChat((previo) => [
      ...previo,
      { id: `${upzCod}-${previo.length}-u`, rol: "usuario", texto: pregunta },
      {
        id: `${upzCod}-${previo.length}-a`,
        rol: "asistente",
        texto: respuesta.respuesta,
        fuentes: respuesta.fuentes,
      },
    ]);
  }

  const nombreUpz = upzFeature?.properties.upz_nombre ?? `UPZ ${upzCod}`;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex h-[85vh] max-h-[820px] flex-col gap-0 p-0 sm:max-w-4xl">
        <DialogHeader className="shrink-0 border-b border-border px-6 py-4">
          <DialogTitle className="font-mono-data text-base tracking-wide">
            {nombreUpz} <span className="text-muted-foreground">· {upzCod}</span>
          </DialogTitle>
          <DialogDescription>
            {upzFeature?.properties.nom_localidad
              ? `Localidad ${upzFeature.properties.nom_localidad} — detalle operacional`
              : "Detalle operacional de la UPZ"}
          </DialogDescription>
        </DialogHeader>

        <Tabs
          value={tabActiva}
          onValueChange={setTabActiva}
          className="flex flex-1 flex-col overflow-hidden"
        >
          <TabsList className="mx-6 mt-3 w-fit shrink-0">
            {PESTANAS.map((pestana) => (
              <TabsTrigger key={pestana.valor} value={pestana.valor}>
                {pestana.etiqueta}
              </TabsTrigger>
            ))}
          </TabsList>

          <div className="flex-1 overflow-y-auto px-6 py-4">
            <TabsContent value="descripcion" className="mt-0">
              <TabDescripcion
                upzCod={upzCod}
                upzFeature={upzFeature}
                cargando={upzGeometriasQuery.isLoading}
              />
            </TabsContent>

            <TabsContent value="prediccion" className="mt-0">
              <TabPrediccion
                prediccion={prediccion}
                explicacion={explicacion}
                isLoading={prediccionCargando}
                error={prediccionError}
              />
            </TabsContent>

            <TabsContent value="sugerencia" className="mt-0">
              <TabSugerencia upzCod={upzCod} shapTop={explicacion?.shap_top3} />
            </TabsContent>

            <TabsContent value="fuentes" className="mt-0">
              <TabFuentes
                mutation={graphragMutation}
                onIrAChatbot={() => setTabActiva("chatbot")}
              />
            </TabsContent>

            <TabsContent value="chatbot" className="mt-0 h-full">
              <TabChatbot
                upzCod={upzCod}
                mutation={graphragMutation}
                historial={historialChat}
                onNuevaRespuesta={handleNuevaRespuesta}
              />
            </TabsContent>
          </div>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
