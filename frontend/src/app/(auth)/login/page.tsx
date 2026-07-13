import type { Metadata } from "next";
import Link from "next/link";
import { LoginForm } from "@/components/auth/LoginForm";
import { Sparkles } from "lucide-react";

export const dynamic = "force-dynamic";

export const metadata: Metadata = { title: "Sign In - Nexora AI" };

export default function LoginPage() {
  return (
    <div className="flex min-h-screen">
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-sm space-y-6">
          <div className="flex items-center gap-2 justify-center">
            <Sparkles className="h-6 w-6 text-primary" />
            <span className="text-xl font-bold">Nexora AI</span>
          </div>
          <div className="text-center">
            <h1 className="text-2xl font-bold">Welcome back</h1>
            <p className="text-sm text-muted-foreground mt-1">Sign in to your account</p>
          </div>
          <LoginForm />
          <p className="text-center text-sm text-muted-foreground">
            Don&apos;t have an account?{" "}
            <Link href="/register" className="text-primary hover:underline">Sign up</Link>
          </p>
        </div>
      </div>
      <div className="hidden lg:flex flex-1 bg-gradient-to-br from-primary/20 via-primary/5 to-background items-center justify-center p-8">
        <div className="max-w-md text-center">
          <h2 className="text-3xl font-bold mb-4">AI-Powered Proposals</h2>
          <p className="text-muted-foreground">Create winning proposals faster with AI assistance. Track opportunities, manage reviews, and close more deals.</p>
        </div>
      </div>
    </div>
  );
}
