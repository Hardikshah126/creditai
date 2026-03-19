import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { LogOut } from "lucide-react";
import { clearToken, getUser } from "@/lib/api";

const navLinks = [
  { label: "Applicants", path: "/lender" },
  { label: "Analytics", path: "/lender/analytics" },
];

const LenderShell = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const user = getUser();
  const initials = user?.name?.split(" ").map((n: string) => n[0]).join("").slice(0, 2).toUpperCase() || "L";

  const handleLogout = () => {
    clearToken();
    navigate("/signup");
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-20 bg-card/80 backdrop-blur-sm border-b border-border">
        <div className="max-w-6xl mx-auto flex items-center justify-between px-6 h-16">
          <div className="flex items-center gap-8">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-sm">C</span>
              </div>
              <span className="font-bold text-lg text-foreground tracking-tight">CreditAI</span>
            </Link>
            <nav className="hidden md:flex items-center gap-1">
              {navLinks.map((link) => (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                    location.pathname === link.path
                      ? "text-primary bg-primary/10"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {link.label}
                </Link>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-muted-foreground hidden sm:block">{user?.name || "Lender"}</span>
            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
              <span className="text-sm font-semibold text-primary">{initials}</span>
            </div>
            <button
              onClick={handleLogout}
              className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              title="Log out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </header>
      <main className="max-w-6xl mx-auto p-6 fade-in">
        <Outlet />
      </main>
    </div>
  );
};

export default LenderShell;