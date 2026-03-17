export const applicant = {
  name: "Amara Osei",
  country: "Ghana",
  score: 72,
  riskTier: "medium" as const,
  documentsUploaded: 2,
  reportGenerated: true,
  phone: "+233 24 123 4567",
  email: "amara.osei@email.com",
};

export const lenderApplicants = [
  { id: "1", name: "Amara Osei", score: 72, riskTier: "medium" as const, country: "Ghana", date: "Mar 9, 2026", sources: ["Utility Bill", "Mobile Recharge"] },
  { id: "2", name: "Priya Nair", score: 85, riskTier: "low" as const, country: "India", date: "Mar 8, 2026", sources: ["Rent Receipt", "Utility Bill", "Transaction Statement"] },
  { id: "3", name: "Carlos Mendez", score: 48, riskTier: "high" as const, country: "Mexico", date: "Mar 7, 2026", sources: ["Mobile Recharge"] },
  { id: "4", name: "Fatima Al-Rashid", score: 91, riskTier: "low" as const, country: "Nigeria", date: "Mar 6, 2026", sources: ["Utility Bill", "Rent Receipt", "Mobile Recharge"] },
  { id: "5", name: "Budi Santoso", score: 63, riskTier: "medium" as const, country: "Indonesia", date: "Mar 5, 2026", sources: ["Transaction Statement", "Utility Bill"] },
];

export const scoreBreakdown = [
  { title: "Utility Payments", icon: "Zap", contribution: 24, strength: "strong" as const, percent: 80, detail: "18 months of consistent payments" },
  { title: "Mobile Recharge", icon: "Smartphone", contribution: 18, strength: "good" as const, percent: 65, detail: "Regular monthly recharges detected" },
  { title: "Transaction Activity", icon: "ArrowLeftRight", contribution: 16, strength: "moderate" as const, percent: 55, detail: "Some gaps in transaction history" },
  { title: "Income Stability", icon: "TrendingUp", contribution: 14, strength: "moderate" as const, percent: 50, detail: "Self-reported stable income" },
];

export const positiveSignals = [
  "Paid electricity bills consistently for 18 months",
  "Mobile recharge shows regular spending behavior",
  "No large unexplained gaps in payment history",
];

export const improvementAreas = [
  "Upload more months of transaction history",
  "Add a second utility bill type",
  "Consistent income documentation would help",
];

export const recentActivity = [
  { action: "Uploaded utility bill", time: "2 hours ago" },
  { action: "Completed AI questionnaire", time: "1 day ago" },
  { action: "Created account", time: "2 days ago" },
];

export const countries = ["Ghana", "India", "Mexico", "Nigeria", "Indonesia", "Kenya", "Philippines", "Bangladesh", "Tanzania", "Colombia"];
