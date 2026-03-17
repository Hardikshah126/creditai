import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { FileText, MessageCircle, Upload, CheckCircle, Loader2 } from "lucide-react";
import { getHistory } from "@/lib/api";

const iconMap: Record<string, any> = {
  score_generated: CheckCircle,
  chat_completed: MessageCircle,
  documents_analyzed: FileText,
  document_uploaded: Upload,
  submission_created: FileText,
  account_created: CheckCircle,
};

const typeMap: Record<string, string> = {
  score_generated: "success",
  account_created: "success",
};

const History = () => {
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getHistory()
      .then(setHistory)
      .catch(() => setHistory([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-foreground">Application History</h2>
        <p className="text-muted-foreground mt-1">Your complete activity timeline.</p>
      </div>

      {history.length === 0 ? (
        <Card className="p-12 text-center">
          <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="font-medium text-foreground">No activity yet</p>
          <p className="text-sm text-muted-foreground mt-1">Upload documents to get started.</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {history.map((item, idx) => {
            const Icon = iconMap[item.event_type] || FileText;
            const isSuccess = typeMap[item.event_type] === "success";
            const date = new Date(item.created_at).toLocaleString("en-IN", {
              month: "short", day: "numeric", year: "numeric",
              hour: "2-digit", minute: "2-digit",
            });
            return (
              <Card key={idx} className="p-4 flex items-start gap-4">
                <div className={`p-2 rounded-lg flex-shrink-0 ${isSuccess ? "bg-success/10" : "bg-muted"}`}>
                  <Icon className={`h-4 w-4 ${isSuccess ? "text-success" : "text-muted-foreground"}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground">{item.action}</p>
                  <p className="text-xs text-muted-foreground">{item.detail}</p>
                </div>
                <span className="text-xs text-muted-foreground whitespace-nowrap">{date}</span>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default History;