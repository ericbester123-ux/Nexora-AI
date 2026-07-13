"use client";

import { cn } from "@/lib/utils";

interface SyncStatusIndicatorProps {
  status: string;
  lastSyncAt: string | null;
  errorMessage?: string | null;
  className?: string;
}

function formatTimeAgo(dateString: string): string {
  const now = new Date();
  const date = new Date(dateString);
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return "Just now";
  if (diffMins < 60) return `${diffMins} min ago`;
  if (diffHours < 24) return `${diffHours} hours ago`;
  if (diffDays < 7) return `${diffDays} days ago`;
  return date.toLocaleDateString();
}

export function SyncStatusIndicator({ status, lastSyncAt, errorMessage, className }: SyncStatusIndicatorProps) {
  const statusConfig: Record<string, { label: string; color: string }> = {
    never: { label: "Never synced", color: "text-gray-500" },
    syncing: { label: "Syncing...", color: "text-blue-600" },
    healthy: { label: "Healthy", color: "text-green-600" },
    error: { label: "Error", color: "text-red-600" },
    completed: { label: "Completed", color: "text-green-600" },
    completed_with_errors: { label: "Completed with errors", color: "text-yellow-600" },
    failed: { label: "Failed", color: "text-red-600" },
    in_progress: { label: "In progress", color: "text-blue-600" },
  };

  const config = statusConfig[status] || { label: status, color: "text-gray-500" };

  return (
    <div className={cn("text-sm", className)}>
      <div className="flex items-center gap-2">
        <span className={cn("h-2 w-2 rounded-full inline-block", {
          "bg-green-500": status === "healthy" || status === "completed",
          "bg-blue-500 animate-pulse": status === "syncing" || status === "in_progress",
          "bg-red-500": status === "error" || status === "failed",
          "bg-yellow-500": status === "completed_with_errors",
          "bg-gray-400": status === "never",
        })} />
        <span className={cn("font-medium", config.color)}>{config.label}</span>
      </div>
      {lastSyncAt && (
        <p className="text-xs text-muted-foreground mt-0.5 ml-4">
          Last sync: {formatTimeAgo(lastSyncAt)}
        </p>
      )}
      {errorMessage && (
        <p className="text-xs text-red-600 mt-0.5 ml-4">{errorMessage}</p>
      )}
    </div>
  );
}
