import type { Metadata } from "next";
import Link from "next/link";
import { LoginForm } from "@/components/auth/LoginForm";

export const dynamic = "force-dynamic";

export const metadata: Metadata = { title: "Sign In - Nexora AI" };

export default function LoginPage() {
  return (
    <div className="relative flex min-h-screen overflow-hidden bg-background">
      <div className="fixed inset-0 bg-grid opacity-40" />
      <div className="fixed inset-0 bg-glow" />
      <div className="fixed top-1/4 left-1/4 h-96 w-96 rounded-full bg-primary/5 blur-3xl animate-float" />
      <div className="fixed bottom-1/4 right-1/4 h-64 w-64 rounded-full bg-emerald-400/5 blur-3xl animate-float" style={{ animationDelay: "-3s" }} />

      <div className="relative flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-sm space-y-8">
          <div className="flex flex-col items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-emerald-400 shadow-lg shadow-primary/25 animate-pulse-glow">
              <svg className="h-6 w-6 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
              </svg>
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-foreground to-foreground/60 bg-clip-text text-transparent">Nexora AI</span>
          </div>

          <div className="text-center">
            <h1 className="text-3xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">Welcome back</h1>
            <p className="text-sm text-muted-foreground mt-2">Sign in to your account to continue</p>
          </div>

          <div className="glass-card rounded-2xl p-6 space-y-6">
            <LoginForm />
          </div>

          <p className="text-center text-sm text-muted-foreground">
            Don&apos;t have an account?{" "}
            <Link href="/register" className="text-primary hover:text-primary/80 font-medium transition-colors">Sign up</Link>
          </p>
        </div>
      </div>

      <div className="relative hidden lg:flex flex-1 items-center justify-center p-8">
        <div className="relative">
          <div className="absolute inset-0 bg-gradient-to-r from-primary/20 via-emerald-400/10 to-transparent blur-3xl" />
          <div className="relative glass-card rounded-3xl p-10 max-w-lg text-center space-y-6">
            <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/20 to-emerald-400/20 border border-primary/10">
              <svg className="h-8 w-8 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
              </svg>
            </div>
            <h2 className="text-3xl font-bold bg-gradient-to-r from-foreground to-foreground/60 bg-clip-text text-transparent">AI-Powered Freelancing</h2>
            <p className="text-muted-foreground leading-relaxed">
              Discover projects, generate winning proposals with AI, and manage your freelance career from one intelligent dashboard.
            </p>
            <div className="grid grid-cols-3 gap-4 pt-4">
              {["Projects", "Proposals", "Analytics"].map((label) => (
                <div key={label} className="rounded-xl bg-white/5 border border-white/5 p-3 text-center">
                  <div className="text-sm font-medium text-foreground/80">{label}</div>
                  <div className="text-xs text-emerald-400 mt-0.5">AI-Powered</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
