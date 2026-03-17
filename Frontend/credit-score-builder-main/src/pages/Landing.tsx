import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Shield, Lock, FileCheck, Globe, Upload, Bot, Award, Check, Building2, User } from "lucide-react";
import ScoreGauge from "@/components/ScoreGauge";

const Landing = () => {
  const scrollToHow = () => {
    document.getElementById("how-it-works")?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Navbar */}
      <nav className="sticky top-0 z-50 bg-card/80 backdrop-blur-sm border-b border-border">
        <div className="max-w-6xl mx-auto flex items-center justify-between px-6 h-16">
          <div className="flex items-center gap-8">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-sm">C</span>
              </div>
              <span className="font-bold text-lg text-foreground tracking-tight">CreditAI</span>
            </Link>
            <div className="hidden md:flex items-center gap-6">
              <button onClick={scrollToHow} className="text-sm text-muted-foreground hover:text-foreground transition-colors">How it works</button>
              <Link to="/signup?role=lender" className="text-sm text-muted-foreground hover:text-foreground transition-colors">For Lenders</Link>
              <span className="text-sm text-muted-foreground hover:text-foreground transition-colors cursor-pointer">About</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/signup?login=true">
              <Button variant="ghost" size="sm">Log in</Button>
            </Link>
            <Link to="/signup">
              <Button size="sm">Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 py-20 lg:py-28">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div>
            <Badge variant="secondary" className="mb-4 text-xs font-medium">AI-Powered · Free to use</Badge>
            <h1 className="text-4xl lg:text-5xl font-bold tracking-tight text-foreground leading-tight mb-4">
              A Credit Score Built Around Your Real Life
            </h1>
            <p className="text-lg text-muted-foreground leading-relaxed mb-8 max-w-lg">
              No credit card history? No problem. Upload your utility bills, rent receipts, or mobile transactions and get an AI-generated credit report lenders actually trust.
            </p>

            {/* Role selection CTA */}
            <div className="grid sm:grid-cols-2 gap-3 mb-8 max-w-lg">
              <Link to="/signup?role=applicant">
                <Card className="p-4 hover:border-primary hover:shadow-md transition-all cursor-pointer group">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                      <User className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <p className="font-semibold text-foreground text-sm">I'm an Applicant</p>
                      <p className="text-xs text-muted-foreground">Get my credit score</p>
                    </div>
                  </div>
                </Card>
              </Link>
              <Link to="/signup?role=lender">
                <Card className="p-4 hover:border-primary hover:shadow-md transition-all cursor-pointer group">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                      <Building2 className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <p className="font-semibold text-foreground text-sm">I'm a Lender</p>
                      <p className="text-xs text-muted-foreground">View applicant reports</p>
                    </div>
                  </div>
                </Card>
              </Link>
            </div>

            <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
              <span className="flex items-center gap-1.5">🔒 Encrypted & Secure</span>
              <span className="flex items-center gap-1.5">⚡ Score in under 3 minutes</span>
              <span className="flex items-center gap-1.5">🌍 Available in India</span>
            </div>
          </div>
          <div className="flex justify-center">
            <Card className="p-8 shadow-lg max-w-xs w-full">
              <div className="flex justify-center mb-4">
                <ScoreGauge score={74} size={180} />
              </div>
              <div className="text-center mb-4">
                <Badge variant="secondary" className="bg-success/10 text-success border-success/20">Low Risk</Badge>
                <p className="text-xs text-muted-foreground mt-2">Generated just now</p>
              </div>
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-foreground">
                  <Check className="h-4 w-4 text-success" /> Utility payments on time
                </div>
                <div className="flex items-center gap-2 text-sm text-foreground">
                  <Check className="h-4 w-4 text-success" /> Regular mobile recharges
                </div>
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="bg-card border-y border-border">
        <div className="max-w-6xl mx-auto px-6 py-20">
          <h2 className="text-3xl font-bold tracking-tight text-foreground text-center mb-4">Three steps to your credit score</h2>
          <p className="text-center text-muted-foreground mb-12 max-w-lg mx-auto">Simple, fast, and completely free.</p>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { icon: Upload, title: "Upload Your Documents", body: "Share utility bills, rent receipts, or mobile recharge history. Any 2 documents is enough to start." },
              { icon: Bot, title: "AI Reads Your Financial Behavior", body: "Our AI agent reads your documents, extracts payment patterns, and asks a few quick follow-up questions." },
              { icon: Award, title: "Get Your Credit Report", body: "Receive a score from 0–100 with a plain-English explanation you can share directly with lenders." },
            ].map((step, idx) => (
              <Card key={idx} className="p-6 text-center relative">
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
                  <step.icon className="h-6 w-6 text-primary" />
                </div>
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs font-bold flex items-center justify-center">
                  {idx + 1}
                </div>
                <h3 className="font-semibold text-foreground mb-2">{step.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{step.body}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Social Proof */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <h2 className="text-3xl font-bold tracking-tight text-foreground text-center mb-12">Trusted across emerging markets</h2>
        <div className="grid md:grid-cols-3 gap-6">
          {[
            { value: "1.4B+", label: "People with no credit history globally" },
            { value: "3 min", label: "Average time to generate a score" },
            { value: "94%", label: "Lender acceptance rate in pilots" },
          ].map((stat) => (
            <Card key={stat.value} className="p-8 text-center">
              <p className="text-4xl font-bold text-primary mb-2">{stat.value}</p>
              <p className="text-sm text-muted-foreground">{stat.label}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* Trust Bar */}
      <section className="border-y border-border bg-card">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { icon: Shield, label: "256-bit encryption" },
              { icon: Lock, label: "Data never sold" },
              { icon: FileCheck, label: "Audit trail on every report" },
              { icon: Globe, label: "Made for India" },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-3 justify-center">
                <item.icon className="h-5 w-5 text-primary" />
                <span className="text-sm font-medium text-foreground">{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Banner */}
      <section className="bg-cta-bg">
        <div className="max-w-6xl mx-auto px-6 py-16 text-center">
          <h2 className="text-3xl font-bold tracking-tight text-primary-foreground mb-4">Ready to prove your creditworthiness?</h2>
          <p className="text-primary-foreground/80 mb-8 max-w-md mx-auto">Join thousands who got their first credit score without a credit card.</p>
          <Link to="/signup?role=applicant">
            <Button size="lg" variant="secondary" className="rounded-lg hover:scale-105 transition-transform">
              Start for Free →
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border">
        <div className="max-w-6xl mx-auto px-6 py-10">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-xs">C</span>
              </div>
              <span className="text-sm text-muted-foreground">AI-powered credit scoring for the unbanked.</span>
            </div>
            <div className="flex gap-6 text-sm text-muted-foreground">
              <span className="hover:text-foreground cursor-pointer">About</span>
              <span className="hover:text-foreground cursor-pointer">Privacy</span>
              <span className="hover:text-foreground cursor-pointer">Terms</span>
              <span className="hover:text-foreground cursor-pointer">Contact</span>
            </div>
          </div>
          <p className="text-xs text-muted-foreground text-center mt-6">© 2026 CreditAI. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;