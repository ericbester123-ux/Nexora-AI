"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface ConnectionStatusBadgeProps {
  status: "connected" | "disconnected" | "error" | "syncing";
  className?: string;
}

export function ConnectionStatusBadge({ status, className }: ConnectionStatusBadgeProps) {
  const config = {
    connected: { label: "Connected", class: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" },
    disconnected: { label: "Not Connected", class: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300" },
    error: { label: "Error", class: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200" },
    syncing: { label: "Syncing", class: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200" },
  };

  const c = config[status];

  return (
    <Badge variant="outline" className={cn("font-medium", c.class, className)}>
      <span className={cn(
        "mr-1.5 h-2 w-2 rounded-full inline-block",
        status === "connected" && "bg-green-500",
        status === "disconnected" && "bg-gray-400",
        status === "error" && "bg-red-500",
        status === "syncing" && "bg-blue-500 animate-pulse",
      )} />
      {c.label}
    </Badge>
  );
}
