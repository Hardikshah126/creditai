import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { BarChart2, Upload, MessageCircle, FileText, Clock, Loader2 } from "lucide-react";
import ScoreGauge from "@/components/ScoreGauge";
import { getDashboard, getUser, clearToken } from "@/lib/api";

const Dashboard = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch(() => {
        clearToken();
        navigate("/signup");
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!data) return null;

  const firstName = data.name?.split(" ")[0] || "there";
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  const reportStatus = data.report_generated
    ? "Report Ready"
    : data.latest_submission_id
    ? "Pending Analysis"
    : "Not Started";

  const statusColor = data.report_generated
    ? "text-success"
    : data.latest_submission_id
    ? "text-warning"
    : "text-muted-foreground";

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Welcome Banner */}
      <Card className="p-6 bg-primary/5 border-primary/10">
        <h2 className="text-xl font-bold tracking-tight text-foreground mb-1">
          {greeting}, {firstName}. 👋
        </h2>
        <p className="text-sm text-muted-foreground mb-4">
          Your credit profile is {data.profile_complete_pct}% complete.
        </p>
        <Progress value={data.profile_complete_pct} className="h-2 max-w-md" />
      </Card>

      {/* Score + Stats */}
      <div className="grid sm:grid-cols-3 gap-4">
        {/* Score Card */}
        <Card className="p-6 flex flex-col items-center justify-center text-center">
          {data.report_generated && data.score ? (
            <>
              <ScoreGauge score={data.score} size={120} />
              <p className="text-xs text-muted-foreground mt-2">Current Score</p>
            </>
          ) : (
            <>
              <div className="w-20 h-20 rounded-full border-4 border-muted flex items-center justify-center mb-2">
                <BarChart2 className="h-8 w-8 text-muted-foreground" />
              </div>
              <p className="text-sm font-medium text-foreground">No Score Yet</p>
              <p className="text-xs text-muted-foreground mt-1">Complete the AI chat to get scored</p>
            </>
          )}
        </Card>

        {/* Documents Card */}
        <Card className="p-6 flex flex-col justify-center">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-lg bg-muted">
              <FileText className="h-5 w-5 text-muted-foreground" />
            </div>
            <p className="text-sm font-medium text-muted-foreground">Documents Uploaded</p>
          </div>
          <p className="text-2xl font-bold text-foreground">{data.documents_uploaded}</p>
          <p className="text-xs text-muted-foreground mt-1">of 3 recommended</p>
          <Progress value={(data.documents_uploaded / 3) * 100} className="h-1.5 mt-3" />
        </Card>

        {/* Report Status Card */}
        <Card className="p-6 flex flex-col justify-center">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-lg bg-muted">
              <Clock className="h-5 w-5 text-muted-foreground" />
            </div>
            <p className="text-sm font-medium text-muted-foreground">Report Status</p>
          </div>
          <p className={`text-xl font-bold ${statusColor}`}>{reportStatus}</p>
          {data.report_generated && data.risk_tier && (
            <p className="text-xs text-muted-foreground mt-1 capitalize">{data.risk_tier.toLowerCase()} risk tier</p>
          )}
        </Card>
      </div>

      {/* Quick Actions */}
      <div>
        <h3 className="text-sm font-medium text-muted-foreground mb-3">Quick Actions</h3>
        <div className="grid sm:grid-cols-3 gap-3">
          <Link to="/dashboard/upload">
            <Button variant="outline" className="w-full justify-start gap-2 h-12 rounded-lg">
              <Upload className="h-4 w-4" /> Upload Documents
            </Button>
          </Link>
          <Link to="/dashboard/assistant">
            <Button variant="outline" className="w-full justify-start gap-2 h-12 rounded-lg">
              <MessageCircle className="h-4 w-4" />
              {data.report_generated ? "Chat with AI" : "Continue with AI Assistant"}
            </Button>
          </Link>
          <Link to="/dashboard/report">
            <Button
              variant={data.report_generated ? "default" : "outline"}
              className="w-full justify-start gap-2 h-12 rounded-lg"
            >
              <BarChart2 className="h-4 w-4" />
              {data.report_generated ? "View My Score →" : "View Report"}
            </Button>
          </Link>
        </div>
      </div>

      {/* Recent Activity */}
      <Card className="p-6">
        <h3 className="font-semibold text-foreground mb-4">Recent Activity</h3>
        <div className="space-y-3">
          {!data.recent_activity || data.recent_activity.length === 0 ? (
            <div className="text-center py-6">
              <p className="text-sm text-muted-foreground">No activity yet.</p>
              <Link to="/dashboard/upload">
                <Button variant="outline" size="sm" className="mt-3 rounded-lg">
                  Upload your first document
                </Button>
              </Link>
            </div>
          ) : (
            data.recent_activity.map((item: any, idx: number) => (
              <div key={idx} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                <span className="text-sm text-foreground">{item.action}</span>
                <span className="text-xs text-muted-foreground">{item.time}</span>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
};

export default Dashboard;