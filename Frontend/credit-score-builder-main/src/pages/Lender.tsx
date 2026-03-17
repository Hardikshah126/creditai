import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Search, Users, Loader2 } from "lucide-react";
import RiskBadge from "@/components/RiskBadge";
import { getLenderApplicants } from "@/lib/api";

const Lender = () => {
  const [applicants, setApplicants] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState("all");

  useEffect(() => {
    getLenderApplicants(search || undefined, riskFilter !== "all" ? riskFilter : undefined)
      .then(setApplicants)
      .catch(() => setApplicants([]))
      .finally(() => setLoading(false));
  }, [search, riskFilter]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Applicants</h1>
          <p className="text-muted-foreground text-sm">{applicants.length} total applicants</p>
        </div>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by name..."
              className="pl-9"
            />
          </div>
          <Select value={riskFilter} onValueChange={setRiskFilter}>
            <SelectTrigger className="w-40"><SelectValue placeholder="Risk tier" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Tiers</SelectItem>
              <SelectItem value="LOW">Low Risk</SelectItem>
              <SelectItem value="MEDIUM">Medium Risk</SelectItem>
              <SelectItem value="HIGH">High Risk</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </Card>

      {/* Table - Desktop */}
      <div className="hidden md:block">
        <Card className="overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="text-left p-4 text-sm font-medium text-muted-foreground">Applicant</th>
                <th className="text-left p-4 text-sm font-medium text-muted-foreground">Score</th>
                <th className="text-left p-4 text-sm font-medium text-muted-foreground">Risk Tier</th>
                <th className="text-left p-4 text-sm font-medium text-muted-foreground">Date</th>
                <th className="text-left p-4 text-sm font-medium text-muted-foreground">Data Sources</th>
                <th className="text-right p-4 text-sm font-medium text-muted-foreground">Action</th>
              </tr>
            </thead>
            <tbody>
              {applicants.map((a) => (
                <tr key={a.report_id} className="border-b border-border last:border-0 hover:bg-muted/30 transition-colors">
                  <td className="p-4">
                    <span className="font-medium text-foreground">{a.name}</span>
                  </td>
                  <td className="p-4">
                    <Badge variant="outline" className={
                      a.score > 70 ? "bg-success/10 text-success border-success/20" :
                      a.score >= 40 ? "bg-warning/10 text-warning border-warning/20" :
                      "bg-destructive/10 text-destructive border-destructive/20"
                    }>{a.score}</Badge>
                  </td>
                  <td className="p-4">
                    <RiskBadge tier={a.risk_tier?.toLowerCase()} />
                  </td>
                  <td className="p-4 text-sm text-muted-foreground">
                    {new Date(a.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
                  </td>
                  <td className="p-4">
                    <div className="flex flex-wrap gap-1">
                      {(a.data_sources || []).map((s: string) => (
                        <Badge key={s} variant="secondary" className="text-xs">{s.replace("_", " ")}</Badge>
                      ))}
                    </div>
                  </td>
                  <td className="p-4 text-right">
                    <Link to={`/lender/report/${a.report_id}`}>
                      <Button variant="outline" size="sm" className="rounded-lg">View Report</Button>
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>

      {/* Mobile Cards */}
      <div className="md:hidden space-y-3">
        {applicants.map((a) => (
          <Link key={a.report_id} to={`/lender/report/${a.report_id}`}>
            <Card className="p-4 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-foreground">{a.name}</span>
                <RiskBadge tier={a.risk_tier?.toLowerCase()} />
              </div>
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <span>Score: {a.score}</span>
                <span>{new Date(a.created_at).toLocaleDateString("en-IN")}</span>
              </div>
            </Card>
          </Link>
        ))}
      </div>

      {applicants.length === 0 && (
        <Card className="p-12 text-center">
          <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="font-medium text-foreground">No applicants found</p>
          <p className="text-sm text-muted-foreground mt-1">
            Applicants appear here once they share their report with lenders.
          </p>
        </Card>
      )}
    </div>
  );
};

export default Lender;