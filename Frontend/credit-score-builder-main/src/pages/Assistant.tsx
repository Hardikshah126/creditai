import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import ChatBubble, { TypingIndicator } from "@/components/ChatBubble";
import { sendMessage, getConversation, generateReport, getUser } from "@/lib/api";
import { toast } from "sonner";

interface Message {
  role: "ai" | "user";
  text: string;
  chips?: string[];
}

// Comprehensive completion detection — catches any phrasing Gemini uses
const isCompletionMessage = (text: string): boolean => {
  const lower = text.toLowerCase();
  return (
    lower.includes("generating your credit score") ||
    lower.includes("generating your creditai score") ||
    lower.includes("generating your personalized creditai") ||
    lower.includes("generating your score") ||
    lower.includes("i have everything i need") ||
    lower.includes("i have all the information") ||
    lower.includes("calculating your score") ||
    lower.includes("score right away") ||
    lower.includes("score now") ||
    lower.includes("all the information i needed") ||
    lower.includes("that's all the information") ||
    lower.includes("that is all the information") ||
    lower.includes("i'll generate") ||
    lower.includes("i will generate") ||
    lower.includes("crunching the numbers") ||
    lower.includes("processing your score")
  );
};

const Assistant = () => {
  const navigate = useNavigate();
  const user = getUser();
  const firstName = user?.name?.split(" ")[0] || "there";
  const submissionId = localStorage.getItem("submissionId");

  const [messages, setMessages] = useState<Message[]>([]);
  const [typing, setTyping] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const [done, setDone] = useState(false);
  const [generatingScore, setGeneratingScore] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const hasStarted = useRef(false);
  const scoreTriggered = useRef(false); // prevent double trigger

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  useEffect(() => {
    if (!submissionId) {
      toast.error("No submission found. Please upload documents first.");
      navigate("/dashboard/upload");
      return;
    }

    getConversation(Number(submissionId))
      .then((conv) => {
        if (conv.messages && conv.messages.length > 0) {
          const loaded: Message[] = conv.messages.map((m: any) => ({
            role: m.role === "assistant" ? "ai" : m.role,
            text: m.content,
            chips: m.chips,
          }));
          setMessages(loaded);
          if (conv.is_complete) {
            setDone(true);
          }
        } else {
          askFirstQuestion();
        }
      })
      .catch(() => {
        askFirstQuestion();
      });
  }, []);

  const askFirstQuestion = () => {
    if (hasStarted.current) return;
    hasStarted.current = true;

    setTimeout(() => {
      setTyping(true);
      setTimeout(async () => {
        setTyping(false);
        try {
          const res = await sendMessage(Number(submissionId), "__start__");
          // Check text + backend is_complete flag + no target_feature means done
          const complete = isCompletionMessage(res.content) ||
            res.is_complete === true ||
            (res.target_feature === null && res.role === "ai" && messages.length > 0);
          appendAI(res.content, res.chips, complete);
        } catch {
          appendAI(`Hi ${firstName} 👋 Let's get started. What is your approximate monthly income in rupees?`);
        }
      }, 1000);
    }, 800);
  };

  const appendAI = (text: string, chips?: string[], isComplete?: boolean) => {
    setMessages((prev) => [...prev, { role: "ai", text, chips }]);
    if (isComplete && !scoreTriggered.current) {
      scoreTriggered.current = true;
      setDone(true);
      handleGenerateScore();
    }
  };

  const handleGenerateScore = async () => {
    setGeneratingScore(true);
    try {
      await generateReport(Number(submissionId));
      setTimeout(() => navigate("/dashboard/report"), 2500);
    } catch (err: any) {
      // Report may already exist — navigate anyway
      setTimeout(() => navigate("/dashboard/report"), 1000);
    }
  };

  const handleAnswer = async (answer: string) => {
    if (typing || done || generatingScore) return;

    setMessages((prev) => [...prev, { role: "user", text: answer }]);
    setInputValue("");
    setTyping(true);

    try {
      const res = await sendMessage(Number(submissionId), answer);
      setTyping(false);

      // Triple-check completion: text pattern, backend flag, or no target_feature left
      const complete =
        isCompletionMessage(res.content) ||
        res.is_complete === true ||
        res.target_feature === null && isCompletionMessage(res.content);

      appendAI(res.content, res.chips, complete);
    } catch (err: any) {
      setTyping(false);
      toast.error(err.message || "Failed to send message");
    }
  };

  const handleSend = () => {
    if (!inputValue.trim() || typing || done) return;
    handleAnswer(inputValue.trim());
  };

  const lastMessage = messages[messages.length - 1];
  const showChips = lastMessage?.role === "ai" && lastMessage?.chips && !done && !typing;

  return (
    <div className="max-w-2xl mx-auto flex flex-col h-[calc(100vh-10rem)]">
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {messages.map((msg, idx) => (
          <div key={idx}>
            <ChatBubble role={msg.role} message={msg.text} />
            {msg.role === "ai" && msg.chips && idx === messages.length - 1 && showChips && (
              <div className="flex flex-wrap gap-2 mt-2 ml-11">
                {msg.chips.map((chip) => (
                  <Button
                    key={chip}
                    variant="outline"
                    size="sm"
                    className="rounded-full"
                    onClick={() => handleAnswer(chip)}
                  >
                    {chip}
                  </Button>
                ))}
              </div>
            )}
          </div>
        ))}
        {typing && <TypingIndicator />}
        {generatingScore && (
          <div className="flex justify-center py-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <div className="h-4 w-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
              Calculating your score...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-border pt-4">
        <div className="flex gap-2">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder={done ? "Score generated! Check the Report tab →" : "Type your answer..."}
            disabled={typing || done || generatingScore}
            className="rounded-lg"
          />
          <Button
            onClick={handleSend}
            disabled={typing || !inputValue.trim() || done || generatingScore}
            size="icon"
            className="rounded-lg"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Assistant;