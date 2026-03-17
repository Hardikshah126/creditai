import { useCallback, useState } from "react";
import { CloudUpload, X, FileText, FileImage } from "lucide-react";
import { Button } from "@/components/ui/button";

interface UploadedFile {
  name: string;
  size: number;
  type: string;
  docType: string;
  status: "uploaded" | "processing";
  file: File;  // ← added
}

interface FileUploadZoneProps {
  onUpload: (files: UploadedFile[]) => void;
  files: UploadedFile[];
  onRemove: (index: number) => void;
  selectedDocType: string;
}

const FileUploadZone = ({ onUpload, files, onRemove, selectedDocType }: FileUploadZoneProps) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const droppedFiles = Array.from(e.dataTransfer.files).map((f) => ({
        name: f.name,
        size: f.size,
        type: f.type,
        docType: selectedDocType,
        status: "uploaded" as const,
        file: f,  // ← added
      }));
      onUpload(droppedFiles);
    },
    [onUpload, selectedDocType]
  );

  const handleClick = () => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".pdf,.jpg,.jpeg,.png,.csv";
    input.multiple = true;
    input.onchange = (e) => {
      const selected = Array.from((e.target as HTMLInputElement).files || []).map((f) => ({
        name: f.name,
        size: f.size,
        type: f.type,
        docType: selectedDocType,
        status: "uploaded" as const,
        file: f,  // ← added
      }));
      onUpload(selected);
    };
    input.click();
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / 1048576).toFixed(1) + " MB";
  };

  return (
    <div className="space-y-4">
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={handleClick}
        className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${
          isDragging ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"
        }`}
      >
        <CloudUpload className="h-10 w-10 mx-auto mb-3 text-muted-foreground" />
        <p className="font-medium text-foreground">Drag files here or click to browse</p>
        <p className="text-sm text-muted-foreground mt-1">Accepted: PDF, JPG, PNG, CSV · Max 10MB</p>
      </div>

      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((file, idx) => (
            <div key={idx} className="flex items-center justify-between p-3 bg-card border border-border rounded-lg">
              <div className="flex items-center gap-3">
                {file.type.includes("image") ? (
                  <FileImage className="h-5 w-5 text-muted-foreground" />
                ) : (
                  <FileText className="h-5 w-5 text-muted-foreground" />
                )}
                <div>
                  <p className="text-sm font-medium text-foreground">{file.name}</p>
                  <p className="text-xs text-muted-foreground">{file.docType} · {formatSize(file.size)}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-success font-medium">Uploaded ✓</span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={(e) => { e.stopPropagation(); onRemove(idx); }}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FileUploadZone;