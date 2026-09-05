import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  User,
  Bot,
  ExternalLink,
  Clock,
  Sparkles,
  BookOpen,
  ChevronDown,
  ChevronUp,
  FileCode2,
} from "lucide-react";
import { Message, SourceCitation, Artifact } from "@/lib/types";

interface MessageItemProps {
  message: Message;
  onOpenArtifact?: (artifact: Artifact) => void;
}

export const MessageItem: React.FC<MessageItemProps> = ({
  message,
  onOpenArtifact,
}) => {
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [selectedSource, setSelectedSource] = useState<SourceCitation | null>(null);

  const isUser = message.role === "user";

  return (
    <div className={`py-4 px-4 sm:px-6 ${isUser ? "bg-slate-900/30" : "bg-slate-900/70"}`}>
      <div className="max-w-3xl mx-auto flex gap-3.5">
        {/* Avatar */}
        <div className="flex-shrink-0 mt-0.5">
          {isUser ? (
            <div className="w-7 h-7 rounded-full bg-slate-700 flex items-center justify-center text-slate-300">
              <User className="w-4 h-4" />
            </div>
          ) : (
            <div className="w-7 h-7 rounded-full bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <Bot className="w-4 h-4" />
            </div>
          )}
        </div>

        {/* Message Content Container */}
        <div className="flex-1 min-w-0 space-y-3">
          {/* Header Metadata */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-200">
              {isUser ? "You" : "Lenny Growth Assistant"}
            </span>
            {!isUser && message.provider && (
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">
                {message.provider}
              </span>
            )}
            {!isUser && message.mode === "ship30" && (
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
                ★ Ship 30
              </span>
            )}
          </div>

          {/* Body */}
          <div className="prose prose-invert prose-amber max-w-none text-sm leading-relaxed text-slate-200">
            {message.content ? (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  p: ({ children }) => <p className="mb-2.5 last:mb-0">{children}</p>,
                  ul: ({ children }) => <ul className="list-disc pl-5 mb-2.5 space-y-1">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal pl-5 mb-2.5 space-y-1">{children}</ol>,
                  strong: ({ children }) => <strong className="font-semibold text-amber-300">{children}</strong>,
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-2 border-amber-500/50 pl-3 py-0.5 my-2 text-slate-400 italic">
                      {children}
                    </blockquote>
                  ),
                  code: ({ children }) => (
                    <code className="px-1.5 py-0.5 rounded bg-slate-800 text-amber-300 font-mono text-xs">
                      {children}
                    </code>
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            ) : (
              <div className="flex items-center gap-2 text-slate-400 text-xs italic py-1">
                <span className="inline-block w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
                <span>Generating response...</span>
              </div>
            )}
          </div>

          {/* Generated Artifacts Banner */}
          {message.artifacts && message.artifacts.length > 0 && (
            <div className="space-y-2 pt-1">
              {message.artifacts.map((art, idx) => (
                <div
                  key={idx}
                  onClick={() => onOpenArtifact && onOpenArtifact(art)}
                  className="flex items-center justify-between p-3 rounded-lg bg-gradient-to-r from-amber-500/10 via-slate-800 to-slate-800 border border-amber-500/30 hover:border-amber-400/60 cursor-pointer transition-all shadow-sm group"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="p-1.5 rounded bg-amber-500/20 text-amber-400">
                      <Sparkles className="w-4 h-4" />
                    </div>
                    <div className="truncate">
                      <div className="text-xs font-semibold text-slate-100 group-hover:text-amber-300 transition-colors truncate">
                        {art.title}
                      </div>
                      <div className="text-[11px] text-slate-400">
                        {art.type === "html" ? "Interactive HTML Application" : "Ship 30 for 30 Essay"} • Click to view side-by-side
                      </div>
                    </div>
                  </div>
                  <button className="flex items-center gap-1 text-xs font-medium text-amber-400 group-hover:text-amber-300 bg-slate-900/60 px-2.5 py-1 rounded border border-amber-500/20">
                    <FileCode2 className="w-3.5 h-3.5" />
                    <span>Open Artifact</span>
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Sources Citation Bar */}
          {message.sources && message.sources.length > 0 && (
            <div className="pt-1">
              <div className="flex items-center justify-between">
                <button
                  onClick={() => setSourcesOpen(!sourcesOpen)}
                  className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors"
                >
                  <BookOpen className="w-3.5 h-3.5 text-amber-400" />
                  <span>
                    {message.sources.length} Grounded Source{message.sources.length > 1 ? "s" : ""}
                  </span>
                  {sourcesOpen ? (
                    <ChevronUp className="w-3 h-3 ml-0.5" />
                  ) : (
                    <ChevronDown className="w-3 h-3 ml-0.5" />
                  )}
                </button>
              </div>

              {sourcesOpen && (
                <div className="mt-2.5 grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {message.sources.map((src, i) => (
                    <div
                      key={i}
                      onClick={() => setSelectedSource(selectedSource === src ? null : src)}
                      className={`p-2.5 rounded-lg border text-xs cursor-pointer transition-colors ${
                        selectedSource === src
                          ? "bg-slate-800 border-amber-500/50"
                          : "bg-slate-800/40 border-slate-800 hover:border-slate-700"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-200 truncate">
                          {src.guest}
                        </span>
                        <span className="text-[10px] text-amber-400 font-mono flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {src.timestamp}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 truncate mt-0.5">
                        {src.episode}
                      </p>
                      {src.youtube_url && (
                        <a
                          href={src.youtube_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="mt-1.5 inline-flex items-center gap-1 text-[10px] text-sky-400 hover:text-sky-300"
                        >
                          <ExternalLink className="w-3 h-3" />
                          <span>Watch Episode</span>
                        </a>
                      )}
                      {selectedSource === src && (
                        <div className="mt-2 pt-2 border-t border-slate-700 text-[11px] text-slate-300 italic">
                          "{src.text}"
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
