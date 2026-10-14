import { createFileRoute, Outlet, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";

import { DashboardSidebar, useSidebar } from "@/components/dashboard/sidebar";
import { DashboardTopbar } from "@/components/dashboard/topbar";
import { AnimatedBackground } from "@/components/site/animated-background";
import { getCurrentUser } from "@/lib/api";

export const Route = createFileRoute("/dashboard")({
  component: DashboardLayout,
});

function DashboardLayout() {
  const { collapsed, toggle } = useSidebar();
  const navigate = useNavigate();

  const [user, setUser] = useState({
    name: "",
    email: "",
  });

  useEffect(() => {
    // Check if token was passed directly via URL query params
    const params = new URLSearchParams(window.location.search);
    const queryToken = params.get("token");
    if (queryToken) {
      localStorage.setItem("token", queryToken);
      window.history.replaceState({}, document.title, window.location.pathname);
    }

    const token = localStorage.getItem("token");

    if (!token) {
      navigate({ to: "/login" });
      return;
    }

    getCurrentUser(token)
      .then((data) => {
        setUser(data);
      })
      .catch((err) => {
        console.error("Authentication failed:", err);

        localStorage.removeItem("token");

        navigate({ to: "/login" });
      });
  }, [navigate]);


  return (
    <div className="relative flex min-h-screen w-full overflow-hidden bg-background">
      <AnimatedBackground variant="subtle" />

      <DashboardSidebar
        collapsed={collapsed}
        onToggle={toggle}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <DashboardTopbar
          userName={user.name}
        />

        <main className="scrollbar-thin flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}