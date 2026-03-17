import { Zap, Smartphone, ArrowLeftRight, TrendingUp, LucideIcon } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

const iconMap: Record<string, LucideIcon> = { Zap, Smartphone, ArrowLeftRight, TrendingUp };

const strengthConfig = {
  strong: { label: "Strong", className: "bg-success/10 text-success border-success/20 hover:bg-success/10", color: "bg-success" },
  good: { label: "Good", className: "bg-success/10 text-success border-success/20 hover:bg-success/10", color: "bg-success" },
  moderate: { label: "Moderate", className: "bg-warning/10 text-warning border-warning/20 hover:bg-warning/10", color: "bg-warning" },
  weak: { label: "Weak", className: "bg-destructive/10 text-destructive border-destructive/20 hover:bg-destructive/10", color: "bg-destructive" },
};

interface SignalCardProps {
  title: string;
  icon: string;
  contribution: number;
  strength: "strong" | "good" | "moderate" | "weak";
  percent: number;
  detail: string;
}

const SignalCard = ({ title, icon, contribution, strength, percent, detail }: SignalCardProps) => {
  const Icon = iconMap[icon] || Zap;
  const cfg = strengthConfig[strength];

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Card className="p-6 hover:shadow-md transition-shadow cursor-default">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <Icon className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="font-semibold text-foreground">{title}</p>
                <p className="text-sm text-success font-medium">+{contribution} pts</p>
              </div>
            </div>
            <Badge variant="outline" className={cfg.className}>{cfg.label}</Badge>
          </div>
          <Progress value={percent} className="h-2 mb-2" />
          <p className="text-sm text-muted-foreground">{detail}</p>
        </Card>
      </TooltipTrigger>
      <TooltipContent>
        <p>This signal contributes {contribution} points based on {title.toLowerCase()} analysis.</p>
      </TooltipContent>
    </Tooltip>
  );
};

export default SignalCard;
