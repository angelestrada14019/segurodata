import { useEffect, useRef, useState } from "react";
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
import {
  PESTANAS_MODAL_UPZ,
  type MensajeChat,
  type TabModalUpz,
} from "@/components/modal-upz/tipos";
import type { GraphragResponse } from "@/types/api";

interface ModalUpzProps {
  upzCod: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /**
   * Pestaña con la que abre el modal — "descripcion" por defecto (entrada
   * desde el mapa de Módulo 1, `/diagnostico`). Módulo 2 reusa este mismo
   * mapa (`mapa-riesgo.tsx`) y el listado `top10-riesgo.tsx` pasando
   * "prediccion": es la razón de ser de esas dos entradas al modal, ver
   * `routes/modulo2-prediccion.tsx`.
   */
  tabInicial?: TabModalUpz;
}

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
export function ModalUpz({
  upzCod,
  open,
  onOpenChange,
  tabInicial = "descripcion",
}: ModalUpzProps) {
  const [tabActiva, setTabActiva] = useState<string>(tabInicial);
  const [historialChat, setHistorialChat] = useState<MensajeChat[]>([]);

  const graphragMutation = useGraphrag();

  // `graphragMutation` es un objeto nuevo cada render (useMutation) — el
  // efecto de abajo solo debe reaccionar a cambios de `upzCod`, nunca a la
  // identidad de ese objeto (incluirlo entero en deps reiniciaría el
  // historial de chat en CADA render, no solo al cambiar de UPZ). Patrón
  // "ref con el valor más reciente": se actualiza en cada render (fuera del
  // efecto, sin causar re-render) y el efecto lee `.current` — satisface la
  // regla de deps sin reintroducir el problema.
  const graphragMutationRef = useRef(graphragMutation);
  graphragMutationRef.current = graphragMutation;

  // Nueva UPZ → se reinicia la sesión del modal (pestaña activa, historial
  // de chat, mutación graphrag). `tabInicial` entra en deps porque el mapa
  // de Módulo 1 pasa "descripcion" y Módulo 2 pasa "prediccion" — si el
  // usuario cierra el modal de una UPZ y abre otra distinta desde el otro
  // módulo en la misma sesión de navegación, debe respetar la pestaña que
  // corresponde a esa entrada, no quedarse pegado a la anterior.
  useEffect(() => {
    setTabActiva(tabInicial);
    setHistorialChat([]);
    graphragMutationRef.current.reset();
  }, [upzCod, tabInicial]);

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
            {PESTANAS_MODAL_UPZ.map((pestana) => (
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
