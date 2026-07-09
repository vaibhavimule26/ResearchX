import { createFileRoute, Outlet } from "@tanstack/react-router";
import { DashboardSidebar, useSidebar } from "@/components/dashboard/sidebar";
import { DashboardTopbar } from "@/components/dashboard/topbar";
import { AnimatedBackground } from "@/components/site/animated-background";

export const Route = createFileRoute("/dashboard")({
  component: DashboardLayout,
});

function DashboardLayout() {
  const { collapsed, toggle } = useSidebar();
  return (
    <div className="relative flex min-h-screen w-full overflow-hidden bg-background">
      <AnimatedBackground variant="subtle" />
      <DashboardSidebar collapsed={collapsed} onToggle={toggle} />
      <div className="flex min-w-0 flex-1 flex-col">
        <DashboardTopbar />
        <main className="scrollbar-thin flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
