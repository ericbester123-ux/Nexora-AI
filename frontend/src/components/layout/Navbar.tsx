"use client";

import { Bell } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/shared/ThemeToggle";
import { useAuthStore } from "@/store/auth-store";

export function Navbar() {
  const { user } = useAuthStore();
  const initials = user?.full_name?.split(" ").map((n) => n[0]).join("").toUpperCase() || "U";

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-6">
      <div>
        <h2 className="text-lg font-semibold">Welcome back{user ? `, ${user.full_name}` : ""}</h2>
        <p className="text-sm text-muted-foreground">Here&apos;s what&apos;s happening today.</p>
      </div>
      <div className="flex items-center gap-3">
        <ThemeToggle />
        <Button variant="ghost" size="icon"><Bell className="h-5 w-5" /></Button>
        <Avatar className="h-8 w-8">
          <AvatarFallback className="text-xs bg-primary text-primary-foreground">{initials}</AvatarFallback>
        </Avatar>
      </div>
    </header>
  );
}
