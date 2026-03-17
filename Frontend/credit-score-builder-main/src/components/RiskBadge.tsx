import { Badge } from "@/components/ui/badge";

interface RiskBadgeProps {
  tier: "low" | "medium" | "high";
}

const config = {
  low: { label: "Low Risk", className: "bg-success/10 text-success border-success/20 hover:bg-success/10" },
  medium: { label: "Medium Risk", className: "bg-warning/10 text-warning border-warning/20 hover:bg-warning/10" },
  high: { label: "High Risk", className: "bg-destructive/10 text-destructive border-destructive/20 hover:bg-destructive/10" },
};

const RiskBadge = ({ tier }: RiskBadgeProps) => {
  const { label, className } = config[tier];
  return <Badge variant="outline" className={className}>{label}</Badge>;
};

export default RiskBadge;
