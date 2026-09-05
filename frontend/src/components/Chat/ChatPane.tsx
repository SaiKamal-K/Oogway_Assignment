import React, { useState, useRef, useEffect } from "react";
import { Send, Square, Sparkles, HelpCircle, Flame, Compass } from "lucide-react";
import { Message, Artifact } from "@/lib/types";
import { MessageItem } from "./MessageItem";

interface ChatPaneProps {
  messages: Message[];
  isStreaming: boolean;
  statusText: string;
  onSendMessage: (text: string, mode: "default" | "ship30") => void;
  onStopStreaming: () => void;
  onOpenArtifact: (artifact: Artifact) => void;
}

export const ChatPane: React.FC<ChatPaneProps> = ({
  messages,
  isStreaming,
  statusText,
  onSendMessage,
  onStopStreaming,
  onOpenArtifact,
}) => {
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<"default" | "ship30">("default");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, statusText]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    onSendMessage(input, mode);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const samplePrompts = [
    {
      title: "Onboarding Leverage",
      desc: "Adam Fishman on why onboarding is the 100% lever",
      prompt: "What is Adam Fishman's view on onboarding and why is it a 100% growth lever?",
      targetMode: "default" as const,
    },
    {
      title: "Ship 30 Essay: PLG",
      desc: "Transform Elena Verna's B2B growth loops into an essay",
      prompt: "Write a Ship 30 for 30 essay on why B2B companies are shifting from sales-led to product-led growth based on Elena Verna's insights.",
      targetMode: "ship30" as const,
    },
    {
      title: "High Agency PMs",
      desc: "Shreyas Doshi's radical frameworks for career progression",
      prompt: "How does Shreyas Doshi define high-agency behavior and what is his L/M/H effort framework?",
      targetMode: "default" as const,
    },
    {
      title: "Product Marketing",
      desc: "Brian Chesky on Airbnb's transition away from traditional PM",
      prompt: "Why did Brian Chesky eliminate traditional product managers at Airbnb and what replaced them?",
      targetMode: "default" as const,
    },
  ];

  return (
    <div className="flex flex-col h-full bg-slate-950">
      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center p-6 text-center max-w-xl mx-auto">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-amber-500 to-amber-300 flex items-center justify-center text-slate-950 shadow-lg shadow-amber-500/20 mb-4">
              <Sparkles className="w-6 h-6" />
            </div>
            <h1 className="text-xl font-bold text-slate-100 tracking-tight">
              The Lenny Growth Assistant
            </h1>
            <p className="text-sm text-slate-400 mt-2 max-w-md leading-relaxed">
              Grounded answers and Ship 30 for 30 content directly retrieved from 200+ hours of Lenny's Podcast transcripts.
            </p>

            {/* Starter Suggestion Chips */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full mt-8 text-left">
              {samplePrompts.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setMode(item.targetMode);
                    onSendMessage(item.prompt, item.targetMode);
                  }}
                  className="p-3 rounded-xl bg-slate-900/80 hover:bg-slate-850 border border-slate-800 hover:border-amber-500/40 text-left transition-all group"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-200 group-hover:text-amber-400 transition-colors">
                      {item.title}
                    </span>
                    {item.targetMode === "ship30" && (
                      <span className="text-[10px] uppercase font-bold text-amber-400 bg-amber-500/10 px-1.5 py-0.2 rounded border border-amber-500/20">
                        Ship 30
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                    {item.desc}
                  </p>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="divide-y divide-slate-800/60 pb-8">
            {messages.map((msg) => (
              <MessageItem
                key={msg.id}
                message={msg}
                onOpenArtifact={onOpenArtifact}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-900/60 backdrop-blur">
        <div className="max-w-3xl mx-auto space-y-2.5">
          {/* Mode Selector & Status Header */}
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-1.5 bg-slate-900 rounded-lg p-0.5 border border-slate-800">
              <button
                type="button"
                onClick={() => setMode("default")}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                  mode === "default"
                    ? "bg-slate-800 text-amber-400 shadow-sm border border-slate-700"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Grounded QA
              </button>
              <button
                type="button"
                onClick={() => setMode("ship30")}
                className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                  mode === "ship30"
                    ? "bg-amber-500 text-slate-950 font-semibold shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <Sparkles className="w-3 h-3" />
                <span>Ship 30 for 30 (~1,250 Words)</span>
              </button>
            </div>

            {statusText && (
              <div className="flex items-center gap-1.5 text-xs text-amber-400/90 animate-pulse">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                <span>{statusText}</span>
              </div>
            )}
          </div>

          {/* Form Input */}
          <form
            onSubmit={handleSubmit}
            className="relative flex items-center bg-slate-900 border border-slate-800 focus-within:border-amber-500/60 rounded-xl shadow-inner transition-colors"
          >
            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                mode === "ship30"
                  ? "Describe the growth topic or guest to turn into a 1,250-word Ship 30 essay..."
                  : "Ask anything from Lenny's Podcast (e.g., onboarding, retention, hiring)..."
              }
              className="w-full bg-transparent px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none resize-none max-h-36"
            />

            <div className="pr-2 flex items-center gap-1">
              {isStreaming ? (
                <button
                  type="button"
                  onClick={onStopStreaming}
                  title="Stop generating"
                  className="p-2 rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/30 transition-colors"
                >
                  <Square className="w-4 h-4 fill-current" />
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={!input.trim()}
                  title="Send message"
                  className="p-2 rounded-lg bg-amber-500 disabled:bg-slate-800 text-slate-950 disabled:text-slate-600 font-semibold hover:bg-amber-400 transition-colors disabled:cursor-not-allowed shadow-sm"
                >
                  <Send className="w-4 h-4" />
                </button>
              )}
            </div>
          </form>

          <div className="text-center">
            <span className="text-[11px] text-slate-500">
              Grounded exclusively in Lenny's Podcast transcripts • Press{" "}
              <kbd className="px-1 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px] border border-slate-700">
                Enter
              </kbd>{" "}
              to send,{" "}
              <kbd className="px-1 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px] border border-slate-700">
                Shift+Enter
              </kbd>{" "}
              for newline
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
