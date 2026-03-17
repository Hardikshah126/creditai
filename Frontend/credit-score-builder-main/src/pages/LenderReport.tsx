import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ArrowLeft, Check, ArrowRight, Loader2, ThumbsUp, ThumbsDown } from "lucide-react";
import ScoreGauge from "@/components/ScoreGauge";
import RiskBadge from "@/components/RiskBadge";
import SignalCard from "@/components/SignalCard";
import { getLenderReport, recordDecision } from "@/lib/api";
import { toast } from "sonner";

const LenderReport = () => {
  const { id } = useParams();
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [deciding, setDeciding] = useState(false);

  useEffect(() => {
    getLenderReport(Number(id))
      .then(setReport)
      .catch(() => toast.error("Report not found"))
      .finally(() => setLoading(false));
  }, [id]);

  const handleDecision = async (decision: "APPROVED" | "REJECTED") => {
    setDeciding(true);
    try {
      await recordDecision(Number(id), decision);
      setReport((prev: any) => ({ ...prev, lender_decision: decision }));
      toast.success(decision === "APPROVED" ? "Application approved!" : "Application rejected.");
    } catch {
      toast.error("Failed to record decision");
    } finally {
      setDeciding(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!report) {
    return (
      <div className="text-center py-20">
        <p className="text-muted-foreground">Report not found.</p>
        <Link to="/lender"><Button variant="outline" className="mt-4">Back to Applicants</Button></Link>
      </div>
    );
  }

  const breakdown = typeof report.score_breakdown === "string"
    ? JSON.parse(report.score_breakdown || "[]")
    : (report.score_breakdown || []);
  const positiveSignals = typeof report.positive_signals === "string"
    ? JSON.parse(report.positive_signals || "[]")
    : (report.positive_signals || []);
  const improvementAreas = typeof report.improvement_areas === "string"
    ? JSON.parse(report.improvement_areas || "[]")
    : (report.improvement_areas || []);
  const generatedDate = new Date(report.created_at).toLocaleDateString("en-IN", {
    month: "long", day: "numeric", year: "numeric",
  });

  const decisionColor = {
    APPROVED: "text-success border-success/30 bg-success/10",
    REJECTED: "text-destructive border-destructive/30 bg-destructive/10",
  }[report.lender_decision as string] || "";

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link to="/lender">
          <Button variant="ghost" size="icon" className="rounded-lg">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">{report.user_name}</h1>
          <p className="text-sm text-muted-foreground">India · Report generated {generatedDate}</p>
        </div>
        {report.lender_decision && (
          <span className={`ml-auto text-xs font-semibold px-3 py-1 rounded-full border ${decisionColor}`}>
            {report.lender_decision}
          </span>
        )}
      </div>

      {/* Score */}
      <Card className="p-8 text-center">
        <div className="flex justify-center mb-4">
          <ScoreGauge score={report.score} size={220} />
        </div>
        <RiskBadge tier={report.risk_tier?.toLowerCase()} />
        <p className="text-sm text-muted-foreground mt-2">ML Probability: {(report.ml_probability * 100).toFixed(1)}%</p>
      </Card>

      {/* Report summary */}
      {report.report_text && (
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-3">Credit Summary</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">{report.report_text}</p>
        </Card>
      )}

      {/* Score breakdown */}
      {breakdown.length > 0 && (
        <div>
          <h2 className="text-xl font-bold tracking-tight text-foreground mb-4">Score Breakdown</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            {breakdown.map((signal: any) => (
              <SignalCard key={signal.title} {...signal} />
            ))}
          </div>
        </div>
      )}

      {/* Signals */}
      <div className="grid md:grid-cols-2 gap-4">
        <Card className="p-6 border-l-4 border-l-success">
          <h3 className="font-semibold text-foreground mb-3">Positive Signals</h3>
          <div className="space-y-2">
            {positiveSignals.map((s: string, i: number) => (
              <div key={i} className="flex items-start gap-2">
                <Check className="h-4 w-4 text-success mt-0.5 flex-shrink-0" />
                <span className="text-sm text-muted-foreground">{s}</span>
              </div>
            ))}
          </div>
        </Card>
        <Card className="p-6 border-l-4 border-l-warning">
          <h3 className="font-semibold text-foreground mb-3">Areas to Improve</h3>
          <div className="space-y-2">
            {improvementAreas.map((a: string, i: number) => (
              <div key={i} className="flex items-start gap-2">
                <ArrowRight className="h-4 w-4 text-warning mt-0.5 flex-shrink-0" />
                <span className="text-sm text-muted-foreground">{a}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Lender decision */}
      {!report.lender_decision && (
        <Card className="p-6">
          <h3 className="font-semibold text-foreground mb-4">Make a Decision</h3>
          <div className="flex gap-3">
            <Button
              className="rounded-lg bg-success hover:bg-success/90 text-white gap-2"
              onClick={() => handleDecision("APPROVED")}
              disabled={deciding}
            >
              <ThumbsUp className="h-4 w-4" /> Approve
            </Button>
            <Button
              variant="outline"
              className="rounded-lg text-destructive border-destructive/30 hover:bg-destructive/10 gap-2"
              onClick={() => handleDecision("REJECTED")}
              disabled={deciding}
            >
              <ThumbsDown className="h-4 w-4" /> Reject
            </Button>
          </div>
        </Card>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        <Button
          variant="outline"
          className="rounded-lg"
          onClick={() => { navigator.clipboard.writeText(window.location.href); toast.success("Link copied!"); }}
        >
          Share Report
        </Button>
      </div>

      <p className="text-xs text-muted-foreground">
        Report ID: {report.id} · Powered by CreditAI India
      </p>
    </div>
  );
};

export default LenderReport;