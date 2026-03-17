import { Sparkles } from "lucide-react";

interface ChatBubbleProps {
  role: "ai" | "user";
  message: string;
}

const ChatBubble = ({ role, message }: ChatBubbleProps) => {
  if (role === "ai") {
    return (
      <div className="flex items-start gap-3 max-w-[85%]">
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center">
          <Sparkles className="h-4 w-4 text-primary-foreground" />
        </div>
        <div className="bg-card border border-border rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
          <p className="text-sm text-foreground leading-relaxed">{message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-end">
      <div className="bg-primary rounded-2xl rounded-tr-sm px-4 py-3 max-w-[85%]">
        <p className="text-sm text-primary-foreground leading-relaxed">{message}</p>
      </div>
    </div>
  );
};

export const TypingIndicator = () => (
  <div className="flex items-start gap-3 max-w-[85%]">
    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center">
      <Sparkles className="h-4 w-4 text-primary-foreground" />
    </div>
    <div className="bg-card border border-border rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
      <div className="flex gap-1">
        <span className="w-2 h-2 rounded-full bg-muted-foreground typing-dot" />
        <span className="w-2 h-2 rounded-full bg-muted-foreground typing-dot" />
        <span className="w-2 h-2 rounded-full bg-muted-foreground typing-dot" />
      </div>
    </div>
  </div>
);

export default ChatBubble;
