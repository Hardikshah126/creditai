import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Zap, Home, Smartphone, CreditCard, Loader2 } from "lucide-react";
import StepProgress from "@/components/StepProgress";
import FileUploadZone from "@/components/FileUploadZone";
import { toast } from "sonner";
import { createSubmission, uploadDocument } from "@/lib/api";

interface UploadedFile {
  name: string;
  size: number;
  type: string;
  docType: string;
  status: "uploaded" | "processing";
  file: File;
}

const docTypes = [
  { id: "utility", icon: Zap, label: "Utility Bill", desc: "Electricity, water, gas" },
  { id: "rent", icon: Home, label: "Rent Receipt", desc: "Monthly rent payments" },
  { id: "mobile", icon: Smartphone, label: "Mobile Recharge History", desc: "Prepaid top-ups" },
  { id: "transaction", icon: CreditCard, label: "Transaction Statement", desc: "Bank or mobile money" },
];

const UploadPage = () => {
  const navigate = useNavigate();
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [submissionId, setSubmissionId] = useState<number | null>(null);

  // ── Create submission on first upload ────────────────────────────
  const ensureSubmission = async (): Promise<number> => {
    if (submissionId) return submissionId;
    const sub = await createSubmission();
    setSubmissionId(sub.id);
    return sub.id;
  };

  const handleUpload = async (newFiles: UploadedFile[]) => {
    // Prevent duplicate doc types
    const existingTypes = files.map((f) => f.docType);
    const duplicate = newFiles.find((f) => existingTypes.includes(f.docType));
    if (duplicate) {
      toast.error(`You already uploaded a ${duplicate.docType}`);
      return;
    }

    try {
      const subId = await ensureSubmission();

      for (const uploadedFile of newFiles) {
        await uploadDocument(subId, uploadedFile.file, uploadedFile.docType);
      }

      setFiles((prev) => [...prev, ...newFiles]);
      toast.success("File uploaded successfully!");
    } catch (err: any) {
      toast.error(err.message || "Upload failed");
    }
  };

  const handleRemove = (idx: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleAnalyze = async () => {
    if (!submissionId) {
      toast.error("Please upload documents first");
      return;
    }
    setAnalyzing(true);
    // Store submission ID so Assistant page can use it
    localStorage.setItem("submissionId", String(submissionId));
    navigate("/dashboard/assistant");
  };

  if (analyzing) {
    return (
      <div className="fixed inset-0 z-50 bg-background flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
          <h2 className="text-xl font-bold text-foreground mb-2">Analyzing your documents...</h2>
          <p className="text-sm text-muted-foreground">
            Extracting payment patterns · Identifying signals · Building your profile
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-foreground">Upload Your Financial Documents</h2>
        <p className="text-muted-foreground mt-1">Upload at least 2 document types to generate your score.</p>
      </div>

      <StepProgress steps={["Upload", "AI Analysis", "Credit Score"]} currentStep={0} />

      {/* Document Type Selector */}
      <div>
        <h3 className="text-sm font-medium text-muted-foreground mb-3">Select document type</h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {docTypes.map((doc) => (
            <Card
              key={doc.id}
              onClick={() => setSelectedType(doc.id)}
              className={`p-4 cursor-pointer transition-all hover:shadow-md ${
                selectedType === doc.id ? "ring-2 ring-primary border-primary" : ""
              }`}
            >
              <div className="p-2 rounded-lg bg-primary/10 w-fit mb-3">
                <doc.icon className="h-5 w-5 text-primary" />
              </div>
              <p className="font-medium text-foreground text-sm">{doc.label}</p>
              <p className="text-xs text-muted-foreground">{doc.desc}</p>
            </Card>
          ))}
        </div>
      </div>

      {/* Upload Zone */}
      {selectedType && (
        <FileUploadZone
          onUpload={handleUpload}
          files={files}
          onRemove={handleRemove}
          selectedDocType={docTypes.find((d) => d.id === selectedType)?.label || ""}
        />
      )}

      {/* Uploaded summary */}
      {files.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {files.map((f, i) => (
            <span key={i} className="text-xs bg-primary/10 text-primary px-3 py-1 rounded-full">
              ✓ {f.docType}
            </span>
          ))}
        </div>
      )}

      {/* Analyze Button */}
      <Button
        onClick={handleAnalyze}
        disabled={files.length < 2}
        className="w-full sm:w-auto rounded-lg hover:scale-105 transition-transform"
        size="lg"
      >
        Analyze Documents
      </Button>
      {files.length < 2 && files.length > 0 && (
        <p className="text-xs text-muted-foreground">
          Upload at least {2 - files.length} more document type(s) to continue.
        </p>
      )}
    </div>
  );
};

export default UploadPage;