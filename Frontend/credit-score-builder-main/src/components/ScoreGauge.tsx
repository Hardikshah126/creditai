import { RadialBarChart, RadialBar, PolarAngleAxis } from "recharts";

interface ScoreGaugeProps {
  score: number;
  size?: number;
}

const getColor = (score: number) => {
  if (score > 70) return "#10B981";
  if (score >= 40) return "#F59E0B";
  return "#EF4444";
};

const ScoreGauge = ({ score, size = 200 }: ScoreGaugeProps) => {
  const color = getColor(score);
  const data = [{ value: score, fill: color }];

  return (
    <div className="relative inline-flex items-center justify-center">
      <RadialBarChart
        width={size}
        height={size}
        cx={size / 2}
        cy={size / 2}
        innerRadius={size * 0.35}
        outerRadius={size * 0.45}
        barSize={size * 0.08}
        data={data}
        startAngle={225}
        endAngle={-45}
      >
        <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
        <RadialBar
          background={{ fill: "hsl(var(--muted))" }}
          dataKey="value"
          angleAxisId={0}
          cornerRadius={size * 0.04}
        />
      </RadialBarChart>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-4xl font-bold tracking-tight text-foreground">{score}</span>
        <span className="text-sm text-muted-foreground">out of 100</span>
      </div>
    </div>
  );
};

export default ScoreGauge;
