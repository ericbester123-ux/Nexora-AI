"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import {
  LayoutDashboard,
  Briefcase,
  FileText,
  BarChart3,
  User,
  Settings,
  Compass,
  LogOut,
  Sparkles,
} from "lucide-react";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/jobs", label: "Jobs", icon: Briefcase },
  { href: "/opportunities", label: "Opportunities", icon: Compass },
  { href: "/proposals", label: "Proposals", icon: FileText },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/profile", label: "Profile", icon: User },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { logout } = useAuth();

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-64 flex-col border-r border-white/5 bg-sidebar/95 backdrop-blur-xl">
      <div className="flex items-center gap-2.5 px-6 py-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-emerald-400 shadow-lg shadow-primary/25">
          <Sparkles className="h-4 w-4 text-white" />
        </div>
        <span className="text-lg font-bold bg-gradient-to-r from-foreground to-foreground/60 bg-clip-text text-transparent">Nexora AI</span>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
                isActive
                  ? "text-primary"
                  : "text-sidebar-foreground/60 hover:text-sidebar-foreground"
              )}
            >
              {isActive && (
                <span className="absolute inset-0 rounded-lg bg-gradient-to-r from-primary/15 to-transparent border border-primary/20" />
              )}
              <item.icon className={cn("h-5 w-5 transition-transform duration-200", isActive ? "scale-110" : "group-hover:scale-110")} />
              <span className="relative">{item.label}</span>
              {isActive && <span className="absolute right-2 h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-white/5 p-3">
        <Button
          variant="ghost"
          className="w-full justify-start text-sidebar-foreground/50 hover:text-red-400 hover:bg-red-400/10 transition-all"
          onClick={logout}
        >
          <LogOut className="mr-3 h-4 w-4" /> Logout
        </Button>
      </div>
    </aside>
  );
}
