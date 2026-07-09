import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { MailCheck, ShieldAlert } from "lucide-react";
import { toast } from "sonner";

import { supabase } from "@/lib/supabase";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const loginSchema = z.object({
  email: z.string().email("Ingresa un correo válido"),
});

type LoginForm = z.infer<typeof loginSchema>;

/**
 * Login con Supabase Auth magic link (`signInWithOtp`). Roles se resuelven
 * por dominio de correo en autoprovisioning (@policia.gov.co → COMANDANTE_CAI,
 * @sdscj.gov.co → ANALISTA_SDSCJ, resto → CIUDADANO) — ver skill
 * supabase-segurodata. `?next=` preserva la ruta original tras el login.
 */
export function LoginPage() {
  const [searchParams] = useSearchParams();
  const next = searchParams.get("next") ?? "/diagnostico";
  const [enviado, setEnviado] = useState<string | null>(null);

  const form = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "" },
  });

  async function onSubmit(values: LoginForm) {
    const { error } = await supabase.auth.signInWithOtp({
      email: values.email,
      options: {
        emailRedirectTo: `${window.location.origin}${next}`,
      },
    });

    if (error) {
      toast.error("No se pudo enviar el enlace", {
        description: error.message,
      });
      return;
    }

    setEnviado(values.email);
    toast.success("Revisa tu correo");
  }

  return (
    <div className="flex flex-1 items-center justify-center p-6">
      <Card className="w-full max-w-sm border-border">
        <CardHeader className="items-center text-center">
          <ShieldAlert className="mb-2 h-8 w-8 text-primary" aria-hidden="true" />
          <CardTitle className="font-mono-data tracking-wide">
            Acceso operacional
          </CardTitle>
          <CardDescription>
            Enviamos un enlace de acceso único a tu correo — sin contraseña.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {enviado ? (
            <div
              role="status"
              className="flex flex-col items-center gap-2 rounded-md border border-success/40 bg-success/10 p-4 text-center text-sm"
            >
              <MailCheck className="h-6 w-6 text-success" aria-hidden="true" />
              <p>
                Enviamos un enlace de acceso a <strong>{enviado}</strong>.
                Ábrelo desde este dispositivo para continuar.
              </p>
            </div>
          ) : (
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="flex flex-col gap-4"
                noValidate
              >
                <FormField
                  control={form.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Correo institucional</FormLabel>
                      <FormControl>
                        <Input
                          type="email"
                          placeholder="nombre@dominio.gov.co"
                          autoComplete="email"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <Button
                  type="submit"
                  className="w-full"
                  disabled={form.formState.isSubmitting}
                >
                  {form.formState.isSubmitting
                    ? "Enviando…"
                    : "Enviar enlace de acceso"}
                </Button>
              </form>
            </Form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
