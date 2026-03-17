import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Check, ArrowRight, Loader2, Share2, Download } from "lucide-react";
import ScoreGauge from "@/components/ScoreGauge";
import RiskBadge from "@/components/RiskBadge";
import SignalCard from "@/components/SignalCard";
import { getLatestReport, shareReport } from "@/lib/api";
import { toast } from "sonner";

// Loading skeleton component
const Skeleton = ({ className }: { className?: string }) => (
  <div className={`animate-pulse bg-muted rounded-lg ${className}`} />
);

const ReportSkeleton = () => (
  <div className="max-w-4xl mx-auto space-y-8">
    <Card className="p-8 text-center">
      <div className="flex justify-center mb-4">
        <Skeleton className="w-52 h-52 rounded-full" />
      </div>
      <Skeleton className="h-6 w-28 mx-auto mb-2" />
      <Skeleton className="h-4 w-40 mx-auto" />
    </Card>
    <div className="grid sm:grid-cols-2 gap-4">
      {[1, 2, 3, 4].map((i) => (
        <Skeleton key={i} className="h-28" />
      ))}
    </div>
  </div>
);

const Report = () => {
  const navigate = useNavigate();
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [sharing, setSharing] = useState(false);
  const [shared, setShared] = useState(false);

  useEffect(() => {
    getLatestReport()
      .then((r) => {
        setReport(r);
        setShared(r.is_shared_with_lender);
      })
      .catch(() => {
        toast.error("No report found. Complete the AI assistant first.");
        navigate("/dashboard/assistant");
      })
      .finally(() => setLoading(false));
  }, []);

  const handleShare = async () => {
    if (shared) {
      toast.info("Already shared with lenders!");
      return;
    }
    setSharing(true);
    try {
      await shareReport(report.submission_id);
      setShared(true);
      toast.success("Report shared with lenders! They can now view your profile.");
    } catch {
      toast.error("Failed to share report");
    } finally {
      setSharing(false);
    }
  };

  const handleDownloadPdf = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(
        `http://localhost:8000/api/v1/reports/${report.submission_id}/pdf`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!res.ok) throw new Error("Download failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `CreditAI-Report-${report.id}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("PDF downloaded!");
    } catch {
      toast.error("Failed to download PDF");
    }
  };

  if (loading) return <ReportSkeleton />;
  if (!report) return null;

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

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Score Hero */}
      <Card className="p-8 text-center">
        <div className="flex justify-center mb-4">
          <ScoreGauge score={report.score} size={220} />
        </div>
        <div className="flex items-center justify-center gap-3 mb-2">
          <RiskBadge tier={report.risk_tier?.toLowerCase()} />
        </div>
        <p className="text-sm text-muted-foreground">Generated {generatedDate}</p>
      </Card>

      {/* Report Summary */}
      {report.report_text && (
        <Card className="p-6">
          <h2 className="text-lg font-semibold text-foreground mb-3">Your Credit Summary</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">{report.report_text}</p>
        </Card>
      )}

      {/* Score Breakdown */}
      {breakdown.length > 0 && (
        <div>
          <h2 className="text-xl font-bold tracking-tight text-foreground mb-4">
            What's driving your score
          </h2>
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
            {positiveSignals.length > 0 ? positiveSignals.map((signal: string, idx: number) => (
              <div key={idx} className="flex items-start gap-2">
                <Check className="h-4 w-4 text-success mt-0.5 flex-shrink-0" />
                <span className="text-sm text-muted-foreground">{signal}</span>
              </div>
            )) : (
              <p className="text-sm text-muted-foreground">Upload more documents to unlock signals.</p>
            )}
          </div>
        </Card>
        <Card className="p-6 border-l-4 border-l-warning">
          <h3 className="font-semibold text-foreground mb-3">Areas to Improve</h3>
          <div className="space-y-2">
            {improvementAreas.map((area: string, idx: number) => (
              <div key={idx} className="flex items-start gap-2">
                <ArrowRight className="h-4 w-4 text-warning mt-0.5 flex-shrink-0" />
                <span className="text-sm text-muted-foreground">{area}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-3">
        <Button
          variant={shared ? "outline" : "default"}
          className="rounded-lg gap-2"
          onClick={handleShare}
          disabled={sharing || shared}
        >
          {sharing ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Share2 className="h-4 w-4" />
          )}
          {shared ? "Shared with Lenders ✓" : "Share with Lenders"}
        </Button>
        <Button variant="outline" className="rounded-lg gap-2" onClick={handleDownloadPdf}>
          <Download className="h-4 w-4" />
          Download PDF
        </Button>
      </div>

      <p className="text-xs text-muted-foreground">
        Report ID: {report.id} · Submission: {report.submission_id} · Powered by CreditAI India
      </p>
    </div>
  );
};

export default Report;