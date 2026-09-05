import { useState, useCallback, useRef } from "react";
import { Message, SourceCitation, Artifact } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface UseChatStreamProps {
  sessionId: string | null;
  onSessionTitleUpdate?: (newTitle: string) => void;
  onArtifactReceived?: (artifact: Artifact) => void;
}

export function useChatStream({
  sessionId,
  onSessionTitleUpdate,
  onArtifactReceived,
}: UseChatStreamProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [statusText, setStatusText] = useState<string>("");
  const [activeSources, setActiveSources] = useState<SourceCitation[]>([]);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (
      text: string,
      mode: "default" | "ship30" = "default",
      provider: string = "ollama"
    ) => {
      if (!sessionId || !text.trim() || isStreaming) return;

      const userMsgId = `user-${Date.now()}`;
      const assistantMsgId = `asst-${Date.now()}`;

      // Append user message immediately
      const userMessage: Message = {
        id: userMsgId,
        role: "user",
        content: text.trim(),
        mode,
        provider,
        created_at: new Date().toISOString(),
      };

      const initialAssistantMessage: Message = {
        id: assistantMsgId,
        role: "assistant",
        content: "",
        sources: [],
        mode,
        provider,
        artifacts: [],
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage, initialAssistantMessage]);
      setIsStreaming(true);
      setStatusText("Connecting to Lenny Growth Assistant...");
      setActiveSources([]);

      abortControllerRef.current = new AbortController();

      try {
        const response = await fetch(`${API_BASE}/api/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: sessionId,
            message: text.trim(),
            mode,
            provider,
          }),
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) {
          throw new Error(`Chat API responded with ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No response body readable stream");

        const decoder = new TextDecoder("utf-8");
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed.startsWith("data: ")) continue;

            const jsonStr = trimmed.replace(/^data:\s*/, "");
            if (jsonStr === "[DONE]") continue;

            try {
              const data = JSON.parse(jsonStr);

              if (data.type === "status") {
                setStatusText(data.content);
              } else if (data.type === "sources") {
                setActiveSources(data.sources || []);
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMsgId
                      ? { ...m, sources: data.sources }
                      : m
                  )
                );
              } else if (data.type === "token") {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMsgId
                      ? { ...m, content: m.content + data.content }
                      : m
                  )
                );
              } else if (data.type === "artifact") {
                const art: Artifact = data.artifact;
                if (onArtifactReceived) {
                  onArtifactReceived(art);
                }
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMsgId
                      ? {
                          ...m,
                          artifacts: [...(m.artifacts || []), art],
                        }
                      : m
                  )
                );
              } else if (data.type === "done") {
                setStatusText("");
              }
            } catch (err) {
              console.warn("Failed to parse SSE payload line:", jsonStr, err);
            }
          }
        }
      } catch (err: any) {
        if (err.name === "AbortError") {
          console.log("Chat stream aborted by user.");
        } else {
          console.error("Chat streaming error:", err);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMsgId
                ? {
                    ...m,
                    content:
                      m.content +
                      `\n\n*[Connection Error: ${err.message || "Failed to reach backend"}]*`,
                  }
                : m
            )
          );
        }
      } finally {
        setIsStreaming(false);
        setStatusText("");
        abortControllerRef.current = null;
      }
    },
    [sessionId, isStreaming, onArtifactReceived]
  );

  const stopStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
      setStatusText("");
    }
  }, []);

  return {
    messages,
    setMessages,
    isStreaming,
    statusText,
    activeSources,
    sendMessage,
    stopStreaming,
  };
}
