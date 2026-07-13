"use client";

import { useState } from "react";
import Link from "next/link";
import { useAuthStore } from "@/store/auth-store";
import { useRouter } from "next/navigation";
import { CheckCircle2, Sparkles, ArrowRight, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";

export default function PlansPage() {
  const { user, setUser } = useAuthStore();
  const router = useRouter();
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);

  const handleActivatePlan = async () => {
    if (!selectedPlan) return;
    setProcessing(true);
    try {
      // Mock payment processing
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Activate user account
      const res = await fetch("/api/auth/me", {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
        body: JSON.stringify({
          subscription_status: "active",
        }),
      });
      
      if (!res.ok) throw new Error("Failed to activate plan");
      
      const userData = await res.json();
      setUser({ ...user, ...userData, subscription_status: "active", is_active: true });
      
      toast.success(`${selectedPlan} plan activated! Your account is now active.`);
      setSelectedPlan(null);
      router.push("/dashboard");
    } catch (e: any) {
      toast.error(e.message || "Failed to activate plan");
    } finally {
      setProcessing(false);
    }
  };

  const plans = [
    {
      name: "Free",
      price: 0,
      period: "month",
      description: "Perfect for getting started",
      features: [
        "5 AI proposals per month",
        "Basic templates",
        "Job matching",
        "Email support",
      ],
      cta: "Get Started",
      popular: false,
    },
    {
      name: "Pro",
      price: 29,
      period: "month",
      description: "For serious freelancers",
      features: [
        "Unlimited AI proposals",
        "Advanced templates",
        "Priority job matching",
        "Proposal analytics",
        "Priority email support",
        "Custom branding",
      ],
      cta: "Start Pro Trial",
      popular: true,
    },
    {
      name: "Team",
      price: 79,
      period: "month",
      description: "For agencies and teams",
      features: [
        "Everything in Pro",
        "5 team seats included",
        "Team collaboration",
        "Shared templates",
        "Advanced analytics",
        "Dedicated support",
        "API access",
      ],
      cta: "Contact Sales",
      popular: false,
    },
  ];

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-16 max-w-6xl">
        <div className="text-center mb-12">
          <Sparkles className="h-10 w-10 text-primary mx-auto mb-4" />
          <h1 className="text-4xl font-bold mb-4">Choose Your Plan</h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Start free and upgrade when you're ready. All plans include access to
            live Freelancer jobs and AI-powered proposal generation.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {plans.map((plan) => (
            <Card
              key={plan.name}
              className={`relative h-full transition-all ${
                plan.popular
                  ? "border-primary shadow-lg shadow-primary/10"
                  : ""
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="bg-primary text-primary-foreground text-xs font-medium px-3 py-1 rounded-full">
                    Most Popular
                  </span>
                </div>
              )}

              <CardHeader className="text-center">
                <CardTitle className="text-2xl">{plan.name}</CardTitle>
                <div className="mt-2 flex items-baseline justify-center gap-1">
                  <span className="text-4xl font-bold">${plan.price}</span>
                  <span className="text-muted-foreground">/{plan.period}</span>
                </div>
                <p className="text-sm text-muted-foreground mt-2">{plan.description}</p>
              </CardHeader>

              <CardContent className="flex flex-col flex-1">
                <ul className="space-y-3 mb-6 flex-1">
                  {plan.features.map((feature, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <CheckCircle2 className="h-5 w-5 text-primary shrink-0" />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>

                <Button
                  className={`w-full ${
                    plan.popular
                      ? "bg-primary hover:bg-primary/90"
                      : "bg-secondary hover:bg-secondary/80"
                  }`}
                  onClick={() => setSelectedPlan(plan.name)}
                  disabled={plan.name === "Team"}
                >
                  {plan.cta}
                  {plan.name === "Team" && (
                    <ArrowRight className="ml-2 h-4 w-4" />
                  )}
                </Button>

                {plan.price === 0 && (
                  <p className="text-center text-xs text-muted-foreground mt-3">
                    No credit card required
                  </p>
                )}
              </CardContent>
            </Card>
          ))}

        </div>

        {selectedPlan && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
            <Card className="w-full max-w-md">
              <CardHeader className="text-center">
                <CardTitle>Activate {selectedPlan} Plan</CardTitle>
                <p className="text-muted-foreground">
                  Complete your subscription to activate your account
                </p>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button 
                  className="w-full" 
                  size="lg" 
                  onClick={handleActivatePlan}
                  disabled={processing}
                >
                  {processing ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Activating...
                    </>
                  ) : (
                    'Continue to Payment'
                  )}
                </Button>
                <Button variant="outline" className="w-full" onClick={() => setSelectedPlan(null)} disabled={processing}>
                  Cancel
                </Button>
              </CardContent>
            </Card>
          </div>
        )}

        <div className="mt-16 text-center">
          <Separator className="mb-8" />
          <h3 className="text-xl font-semibold mb-4">All plans include</h3>
          <div className="grid md:grid-cols-3 gap-6 text-center">
            <div className="p-4">
              <Sparkles className="h-8 w-8 text-primary mx-auto mb-2" />
              <h4 className="font-semibold">AI Proposals</h4>
              <p className="text-sm text-muted-foreground">
                Generate winning proposals in minutes
              </p>
            </div>
            <div className="p-4">
              <Sparkles className="h-8 w-8 text-primary mx-auto mb-2" />
              <h4 className="font-semibold">Live Jobs</h4>
              <p className="text-sm text-muted-foreground">
                Real-time Freelancer.com opportunities
              </p>
            </div>
            <div className="p-4">
              <Sparkles className="h-8 w-8 text-primary mx-auto mb-2" />
              <h4 className="font-semibold">Human Review</h4>
              <p className="text-sm text-muted-foreground">
                Every proposal requires your approval
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}