"use client";

import { useAuthStore } from "@/store/auth-store";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Settings, CheckCircle2, XCircle, Loader2, RefreshCw, ExternalLink } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { FreelancerConnectButton } from "@/components/auth/FreelancerConnectButton";

export default function ProfilePage() {
  const { user, setUser } = useAuthStore();
  const initials = user?.full_name?.split(" ").map((n) => n[0]).join("").toUpperCase() || "U";
  const [syncing, setSyncing] = useState(false);

  const isConnected = !!user?.freelancer_user_id;

  const handleDisconnect = async () => {
    try {
      const res = await fetch("/api/integrations/freelancer/disconnect", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || data.message || "Failed to disconnect");
      toast.success(data.message);
      setUser(user ? { ...user, freelancer_user_id: null, freelancer_connected_at: null, freelancer_token_expires_at: null } : null);
    } catch (e: any) {
      toast.error(e.message);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      const res = await fetch("/api/integrations/freelancer/sync", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: "", limit: 20 }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || data.message || "Sync failed");
      toast.success(`${data.opportunities_imported} new, ${data.opportunities_updated} updated`);
    } catch (e: any) {
      toast.error(e.message);
    } finally {
      setSyncing(false);
    }
  };

  const handleFreelancerConnected = (freelancerUserId: string) => {
    if (user) {
      setUser({ ...user, freelancer_user_id: freelancerUserId });
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold">Profile</h1>
        <p className="text-muted-foreground">Manage your account information</p>
      </div>
      <Card>
        <CardHeader className="flex flex-row items-center gap-4">
          <Avatar className="h-16 w-16">
            <AvatarFallback className="text-lg bg-primary text-primary-foreground">{initials}</AvatarFallback>
          </Avatar>
          <div>
            <CardTitle>{user?.full_name || "User"}</CardTitle>
            <p className="text-sm text-muted-foreground">{user?.email}</p>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Full Name</Label>
            <Input defaultValue={user?.full_name || ""} />
          </div>
          <div className="space-y-2">
            <Label>Email</Label>
            <Input defaultValue={user?.email || ""} disabled />
          </div>
          <Separator />

          {/* Freelancer Integration Section */}
          <div className="space-y-4 p-4 bg-muted/50 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Settings className="h-5 w-5 text-muted-foreground" />
                <div>
                  <h3 className="font-medium">Freelancer.com Integration</h3>
                  <p className="text-sm text-muted-foreground">Connect your account to sync projects and bid with AI</p>
                </div>
              </div>
              {isConnected ? (
                <div className="flex items-center gap-2">
                  <span className="flex items-center gap-1 text-green-600 text-sm">
                    <CheckCircle2 className="h-4 w-4" />
                    Connected as {user?.freelancer_user_id}
                  </span>
                  <Button variant="outline" size="sm" onClick={handleSync} disabled={syncing}>
                    {syncing ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <RefreshCw className="h-4 w-4 mr-2" />}
                    Sync Now
                  </Button>
                  <Button variant="destructive" size="sm" onClick={handleDisconnect}>
                    <XCircle className="h-4 w-4 mr-1" />
                    Disconnect
                  </Button>
                </div>
              ) : (
                <FreelancerConnectButton onConnected={handleFreelancerConnected} />
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}