import { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Upload, Bot, Award, Loader2, User, Building2, ArrowLeft } from "lucide-react";
import { countries } from "@/data/dummy";
import { signup, login, getUser } from "@/lib/api";
import { toast } from "sonner";

type Screen = "role" | "form";
type Role = "applicant" | "lender" | null;

const redirectByRole = (role: string, navigate: (path: string) => void) => {
  if (role === "lender") navigate("/lender");
  else navigate("/dashboard");
};

const Signup = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Determine initial screen from URL params
  const roleParam = searchParams.get("role") as Role;
  const loginParam = searchParams.get("login") === "true";

  const [screen, setScreen] = useState<Screen>(roleParam ? "form" : "role");
  const [selectedRole, setSelectedRole] = useState<Role>(roleParam || null);
  const [isLogin, setIsLogin] = useState(loginParam);

  // Form state
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [country, setCountry] = useState("India");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  // Login state
  const [loginIdentifier, setLoginIdentifier] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  const handleRoleSelect = (role: Role) => {
    setSelectedRole(role);
    setScreen("form");
    // Lenders should always login not signup
    if (role === "lender") setIsLogin(true);
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!country) { toast.error("Please select a country"); return; }
    setLoading(true);
    try {
      await signup({ name, phone, country, email: email || undefined, password });
      toast.success("Account created!");
      const user = getUser();
      redirectByRole(user?.role || "applicant", navigate);
    } catch (err: any) {
      toast.error(err.message || "Signup failed");
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(loginIdentifier, loginPassword);
      toast.success("Welcome back!");
      const user = getUser();
      redirectByRole(user?.role || "applicant", navigate);
    } catch (err: any) {
      toast.error(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    { icon: Upload, title: "Upload Documents", desc: "Share utility bills, rent receipts, or mobile transactions." },
    { icon: Bot, title: "AI Analysis", desc: "Our AI reads your financial patterns in minutes." },
    { icon: Award, title: "Get Your Score", desc: "Receive a 0-100 score with a detailed breakdown." },
  ];

  // ── Role Selection Screen ─────────────────────────────────────────────────
  if (screen === "role") {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <div className="w-full max-w-md">
          <Link to="/" className="flex items-center gap-2 justify-center mb-8">
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-sm">C</span>
            </div>
            <span className="font-bold text-lg text-foreground tracking-tight">CreditAI</span>
          </Link>

          <h1 className="text-2xl font-bold tracking-tight text-foreground text-center mb-2">
            How are you using CreditAI?
          </h1>
          <p className="text-sm text-muted-foreground text-center mb-8">
            Choose your role to get started
          </p>

          <div className="space-y-3">
            <Card
              className="p-5 hover:border-primary hover:shadow-md transition-all cursor-pointer group"
              onClick={() => handleRoleSelect("applicant")}
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors flex-shrink-0">
                  <User className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="font-semibold text-foreground">I'm an Applicant</p>
                  <p className="text-sm text-muted-foreground">Upload documents and get my AI credit score</p>
                </div>
              </div>
            </Card>

            <Card
              className="p-5 hover:border-primary hover:shadow-md transition-all cursor-pointer group"
              onClick={() => handleRoleSelect("lender")}
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors flex-shrink-0">
                  <Building2 className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="font-semibold text-foreground">I'm a Lender</p>
                  <p className="text-sm text-muted-foreground">View applicant credit reports and make decisions</p>
                </div>
              </div>
            </Card>
          </div>

          <p className="text-xs text-muted-foreground text-center mt-6">
            Already have an account?{" "}
            <button onClick={() => { setIsLogin(true); setScreen("form"); }} className="text-primary hover:underline">
              Log in
            </button>
          </p>
        </div>
      </div>
    );
  }

  // ── Login / Signup Form Screen ────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-background flex">
      {/* Left Panel */}
      <div className="hidden lg:flex flex-col justify-center w-1/2 bg-primary p-12">
        {selectedRole === "lender" ? (
          <>
            <h2 className="text-2xl font-bold text-primary-foreground mb-4">Lender Portal</h2>
            <p className="text-primary-foreground/80 mb-8">Access applicant credit reports, view AI-generated scores, and make lending decisions in one place.</p>
            <div className="space-y-4">
              {["View all shared applicant reports", "Filter by risk tier", "Approve or reject applications", "Download PDF reports"].map((item, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-primary-foreground/60" />
                  <p className="text-sm text-primary-foreground/80">{item}</p>
                </div>
              ))}
            </div>
          </>
        ) : (
          <>
            <h2 className="text-2xl font-bold text-primary-foreground mb-8">How it works</h2>
            <div className="space-y-8">
              {steps.map((step, idx) => (
                <div key={idx} className="flex gap-4">
                  <div className="w-10 h-10 rounded-lg bg-primary-foreground/10 flex items-center justify-center flex-shrink-0">
                    <step.icon className="h-5 w-5 text-primary-foreground" />
                  </div>
                  <div>
                    <p className="font-semibold text-primary-foreground">{step.title}</p>
                    <p className="text-sm text-primary-foreground/70">{step.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Right Panel */}
      <div className="flex-1 flex items-center justify-center p-6">
        <Card className="w-full max-w-md p-8">
          <div className="mb-6">
            <button
              onClick={() => setScreen("role")}
              className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4 transition-colors"
            >
              <ArrowLeft className="h-3.5 w-3.5" /> Back
            </button>
            <Link to="/" className="flex items-center gap-2 mb-6">
              <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-sm">C</span>
              </div>
              <span className="font-bold text-lg text-foreground tracking-tight">CreditAI</span>
            </Link>

            {/* Role badge */}
            {selectedRole && (
              <div className="flex items-center gap-2 mb-4">
                <div className="flex items-center gap-1.5 text-xs bg-primary/10 text-primary px-2.5 py-1 rounded-full">
                  {selectedRole === "lender" ? <Building2 className="h-3 w-3" /> : <User className="h-3 w-3" />}
                  {selectedRole === "lender" ? "Lender" : "Applicant"}
                </div>
              </div>
            )}

            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              {isLogin ? "Welcome back" : "Create your profile"}
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              {isLogin
                ? selectedRole === "lender" ? "Log in to your lender account." : "Log in to your account."
                : "Get started with your AI credit score."}
            </p>
          </div>

          {/* Login Form */}
          {isLogin ? (
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <Label htmlFor="identifier">Phone or Email</Label>
                <Input
                  id="identifier"
                  value={loginIdentifier}
                  onChange={(e) => setLoginIdentifier(e.target.value)}
                  placeholder={selectedRole === "lender" ? "hardik@lender.com" : "your@email.com"}
                  className="mt-1"
                  required
                />
              </div>
              <div>
                <Label htmlFor="loginPassword">Password</Label>
                <Input
                  id="loginPassword"
                  type="password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  placeholder="••••••••"
                  className="mt-1"
                  required
                />
              </div>
              <Button type="submit" className="w-full rounded-lg" disabled={loading}>
                {loading && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
                {loading ? "Logging in..." : "Log In →"}
              </Button>
            </form>
          ) : (
            /* Signup Form — only for applicants */
            <form onSubmit={handleSignup} className="space-y-4">
              <div>
                <Label htmlFor="name">Full Name</Label>
                <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Hardik Shah" className="mt-1" required />
              </div>
              <div>
                <Label htmlFor="phone">Phone Number</Label>
                <Input id="phone" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+91 98765 43210" className="mt-1" required />
              </div>
              <div>
                <Label>Country</Label>
                <Select value={country} onValueChange={setCountry}>
                  <SelectTrigger className="mt-1"><SelectValue placeholder="Select country" /></SelectTrigger>
                  <SelectContent>
                    {countries.map((c) => (
                      <SelectItem key={c} value={c}>{c}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="email">Email (optional)</Label>
                <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@email.com" className="mt-1" />
              </div>
              <div>
                <Label htmlFor="password">Password</Label>
                <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Min 6 characters" className="mt-1" required />
              </div>
              <Button type="submit" className="w-full rounded-lg hover:scale-105 transition-transform" disabled={loading}>
                {loading && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
                {loading ? "Creating account..." : "Continue →"}
              </Button>
            </form>
          )}

          {/* Toggle login/signup — only for applicants */}
          {selectedRole !== "lender" && (
            <p className="text-sm text-center text-muted-foreground mt-4">
              {isLogin ? (
                <>Don't have a profile?{" "}
                  <button onClick={() => setIsLogin(false)} className="text-primary hover:underline">Sign up</button>
                </>
              ) : (
                <>Already have a profile?{" "}
                  <button onClick={() => setIsLogin(true)} className="text-primary hover:underline">Log in</button>
                </>
              )}
            </p>
          )}
        </Card>
      </div>
    </div>
  );
};

export default Signup;