import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Users, TrendingUp, ThumbsUp, ThumbsDown, Clock, Loader2 } from "lucide-react";
import { apiFetch } from "@/lib/api";

const LenderAnalytics = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch("/lender/analytics")
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!data || data.total === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Analytics</h1>
          <p className="text-muted-foreground text-sm">Overview of all applicant reports</p>
        </div>
        <Card className="p-12 text-center">
          <TrendingUp className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="font-medium text-foreground">No data yet</p>
          <p className="text-sm text-muted-foreground mt-1">Analytics will appear once applicants share their reports.</p>
        </Card>
      </div>
    );
  }

  const approvalRate = data.total > 0 ? Math.round((data.approved / data.total) * 100) : 0;
  const maxBucket = Math.max(...data.score_buckets.map((b: any) => b.count), 1);

  const riskColors = {
    low: "bg-success",
    medium: "bg-warning",
    high: "bg-destructive",
  };

  const decisionColor = (d: string) =>
    d === "APPROVED" ? "text-success bg-success/10" : "text-destructive bg-destructive/10";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Analytics</h1>
        <p className="text-muted-foreground text-sm">Overview of all applicant reports</p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-5">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-primary/10">
              <Users className="h-4 w-4 text-primary" />
            </div>
            <span className="text-sm text-muted-foreground">Total</span>
          </div>
          <p className="text-3xl font-bold text-foreground">{data.total}</p>
          <p className="text-xs text-muted-foreground mt-1">Shared reports</p>
        </Card>

        <Card className="p-5">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-success/10">
              <ThumbsUp className="h-4 w-4 text-success" />
            </div>
            <span className="text-sm text-muted-foreground">Approved</span>
          </div>
          <p className="text-3xl font-bold text-success">{data.approved}</p>
          <p className="text-xs text-muted-foreground mt-1">{approvalRate}% approval rate</p>
        </Card>

        <Card className="p-5">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-destructive/10">
              <ThumbsDown className="h-4 w-4 text-destructive" />
            </div>
            <span className="text-sm text-muted-foreground">Rejected</span>
          </div>
          <p className="text-3xl font-bold text-destructive">{data.rejected}</p>
          <p className="text-xs text-muted-foreground mt-1">Applications declined</p>
        </Card>

        <Card className="p-5">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-warning/10">
              <Clock className="h-4 w-4 text-warning" />
            </div>
            <span className="text-sm text-muted-foreground">Pending</span>
          </div>
          <p className="text-3xl font-bold text-warning">{data.pending}</p>
          <p className="text-xs text-muted-foreground mt-1">Awaiting decision</p>
        </Card>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Score Distribution */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="font-semibold text-foreground">Score Distribution</h2>
            <span className="text-sm text-muted-foreground">Avg: <span className="font-semibold text-foreground">{data.avg_score}</span></span>
          </div>
          <div className="space-y-3">
            {data.score_buckets.map((bucket: any) => (
              <div key={bucket.range} className="flex items-center gap-3">
                <span className="text-xs text-muted-foreground w-14 text-right">{bucket.range}</span>
                <div className="flex-1 bg-muted rounded-full h-6 overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full flex items-center justify-end pr-2 transition-all duration-500"
                    style={{ width: `${Math.max((bucket.count / maxBucket) * 100, bucket.count > 0 ? 8 : 0)}%` }}
                  >
                    {bucket.count > 0 && (
                      <span className="text-xs text-primary-foreground font-medium">{bucket.count}</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Risk Breakdown */}
        <Card className="p-6">
          <h2 className="font-semibold text-foreground mb-6">Risk Tier Breakdown</h2>
          <div className="space-y-4">
            {(["low", "medium", "high"] as const).map((tier) => {
              const count = data.risk_distribution[tier];
              const pct = data.total > 0 ? Math.round((count / data.total) * 100) : 0;
              return (
                <div key={tier}>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-sm font-medium text-foreground capitalize">{tier} Risk</span>
                    <span className="text-sm text-muted-foreground">{count} applicants ({pct}%)</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-3">
                    <div
                      className={`h-3 rounded-full transition-all duration-500 ${riskColors[tier]}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Donut-style summary */}
          <div className="mt-6 pt-4 border-t border-border grid grid-cols-3 gap-2 text-center">
            {(["low", "medium", "high"] as const).map((tier) => (
              <div key={tier}>
                <p className={`text-2xl font-bold ${
                  tier === "low" ? "text-success" : tier === "medium" ? "text-warning" : "text-destructive"
                }`}>{data.risk_distribution[tier]}</p>
                <p className="text-xs text-muted-foreground capitalize">{tier}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Recent Decisions */}
      {data.recent_decisions.length > 0 && (
        <Card className="p-6">
          <h2 className="font-semibold text-foreground mb-4">Recent Decisions</h2>
          <div className="space-y-3">
            {data.recent_decisions.map((d: any, idx: number) => (
              <div key={idx} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-xs font-semibold text-primary">
                    {d.name.charAt(0)}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">{d.name}</p>
                    <p className="text-xs text-muted-foreground">Score: {d.score}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${decisionColor(d.decision)}`}>
                    {d.decision}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {new Date(d.decided_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};

export default LenderAnalytics;