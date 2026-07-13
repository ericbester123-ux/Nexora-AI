import type { Metadata } from "next";
import Link from "next/link";
import { RegisterForm } from "@/components/auth/RegisterForm";
import { Sparkles } from "lucide-react";

export const metadata: Metadata = { title: "Create Account - Nexora AI" };

export default function RegisterPage() {
  return (
    <div className="flex min-h-screen">
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-sm space-y-6">
          <div className="flex items-center gap-2 justify-center">
            <Sparkles className="h-6 w-6 text-primary" />
            <span className="text-xl font-bold">Nexora AI</span>
          </div>
          <div className="text-center">
            <h1 className="text-2xl font-bold">Create an account</h1>
            <p className="text-sm text-muted-foreground mt-1">Get started with Nexora AI</p>
          </div>
          <RegisterForm />
          <p className="text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link href="/login" className="text-primary hover:underline">Sign in</Link>
          </p>
        </div>
      </div>
      <div className="hidden lg:flex flex-1 bg-gradient-to-br from-primary/20 via-primary/5 to-background items-center justify-center p-8">
        <div className="max-w-md text-center">
          <h2 className="text-3xl font-bold mb-4">Join Nexora AI</h2>
          <p className="text-muted-foreground">Start creating professional proposals with the power of AI. Your next opportunity starts here.</p>
        </div>
      </div>
    </div>
  );
}
