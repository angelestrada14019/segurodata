import { Outlet } from "react-router-dom";
import { Navbar } from "@/components/layout/navbar";
import { Toaster } from "@/components/ui/sonner";

export function RootLayout() {
  return (
    <div className="flex min-h-svh flex-col bg-background text-foreground">
      <Navbar />
      <main className="flex flex-1 flex-col">
        <Outlet />
      </main>
      <Toaster richColors position="top-right" />
    </div>
  );
}
