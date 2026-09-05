import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  X,
  Copy,
  Check,
  Download,
  Code2,
  Eye,
  Maximize2,
  Minimize2,
  FileText,
  Sparkles,
} from "lucide-react";
import { Artifact } from "@/lib/types";
import { SandboxedIframe } from "./SandboxedIframe";

interface ArtifactViewerProps {
  artifact: Artifact | null;
  onClose: () => void;
}

export const ArtifactViewer: React.FC<ArtifactViewerProps> = ({
  artifact,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<"preview" | "code">("preview");
  const [copied, setCopied] = useState<boolean>(false);
  const [isExpanded, setIsExpanded] = useState<boolean>(false);

  if (!artifact) return null;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(artifact.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  const handleDownload = () => {
    const ext = artifact.type === "html" ? "html" : "md";
    const filename = `${artifact.title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}.${ext}`;
    const blob = new Blob([artifact.content], {
      type: artifact.type === "html" ? "text/html" : "text/markdown",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div
      className={`flex flex-col h-full bg-slate-900 border-l border-slate-800 transition-all duration-300 z-20 ${
        isExpanded ? "w-full absolute inset-0 z-30" : "w-full"
      }`}
    >
      {/* Artifact Top Bar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-950/60 backdrop-blur">
        <div className="flex items-center gap-2 min-w-0 pr-2">
          <div className="p-1.5 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Sparkles className="w-4 h-4" />
          </div>
          <div className="truncate">
            <h2 className="text-sm font-semibold text-slate-100 truncate">
              {artifact.title}
            </h2>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-slate-800 text-amber-400 border border-amber-500/20">
                {artifact.type === "html" ? "HTML Snippet" : "Ship 30 Essay"}
              </span>
              <span className="text-[11px] text-slate-400">Claude Artifact</span>
            </div>
          </div>
        </div>

        {/* View Switcher & Action Buttons */}
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <div className="flex items-center bg-slate-800 rounded-lg p-0.5 border border-slate-700/60 mr-1">
            <button
              onClick={() => setActiveTab("preview")}
              className={`flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                activeTab === "preview"
                  ? "bg-amber-500 text-slate-950 shadow-sm"
                  : "text-slate-300 hover:text-white"
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              <span>Preview</span>
            </button>
            <button
              onClick={() => setActiveTab("code")}
              className={`flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                activeTab === "code"
                  ? "bg-amber-500 text-slate-950 shadow-sm"
                  : "text-slate-300 hover:text-white"
              }`}
            >
              <Code2 className="w-3.5 h-3.5" />
              <span>Code</span>
            </button>
          </div>

          <button
            onClick={handleCopy}
            title="Copy content"
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 transition-colors"
          >
            {copied ? (
              <Check className="w-4 h-4 text-emerald-400" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </button>

          <button
            onClick={handleDownload}
            title="Download file"
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 transition-colors"
          >
            <Download className="w-4 h-4" />
          </button>

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            title={isExpanded ? "Collapse" : "Expand"}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 transition-colors"
          >
            {isExpanded ? (
              <Minimize2 className="w-4 h-4" />
            ) : (
              <Maximize2 className="w-4 h-4" />
            )}
          </button>

          <button
            onClick={onClose}
            title="Close artifact"
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-red-900/40 text-slate-400 hover:text-red-300 border border-slate-700/60 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Artifact Content Area */}
      <div className="flex-1 overflow-y-auto p-4 bg-slate-950/40">
        {activeTab === "preview" ? (
          artifact.type === "html" ? (
            <SandboxedIframe content={artifact.content} title={artifact.title} />
          ) : (
            <div className="max-w-3xl mx-auto bg-slate-900/90 border border-slate-800 rounded-xl p-6 sm:p-8 shadow-xl text-slate-200">
              <article className="prose prose-invert prose-amber max-w-none space-y-4">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({ children }) => (
                      <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-amber-400 pb-3 border-b border-slate-800 mb-6">
                        {children}
                      </h1>
                    ),
                    h2: ({ children }) => (
                      <h2 className="text-xl font-bold text-slate-100 mt-6 mb-3 flex items-center gap-2">
                        <span className="w-1.5 h-4 bg-amber-500 rounded-full inline-block"></span>
                        {children}
                      </h2>
                    ),
                    h3: ({ children }) => (
                      <h3 className="text-base font-semibold text-slate-200 mt-4 mb-2">
                        {children}
                      </h3>
                    ),
                    p: ({ children }) => (
                      <p className="text-sm leading-relaxed text-slate-300 mb-3">
                        {children}
                      </p>
                    ),
                    ul: ({ children }) => (
                      <ul className="list-disc pl-5 space-y-2 text-sm text-slate-300 my-3">
                        {children}
                      </ul>
                    ),
                    ol: ({ children }) => (
                      <ol className="list-decimal pl-5 space-y-2 text-sm text-slate-300 my-3">
                        {children}
                      </ol>
                    ),
                    strong: ({ children }) => (
                      <strong className="font-semibold text-amber-300">
                        {children}
                      </strong>
                    ),
                    blockquote: ({ children }) => (
                      <blockquote className="border-l-4 border-amber-500/60 pl-4 py-1 italic bg-amber-500/5 rounded-r text-slate-300 my-4">
                        {children}
                      </blockquote>
                    ),
                    hr: () => <hr className="border-slate-800 my-6" />,
                  }}
                >
                  {artifact.content}
                </ReactMarkdown>
              </article>
            </div>
          )
        ) : (
          <div className="h-full rounded-lg border border-slate-800 bg-slate-950 p-4 font-mono text-xs text-slate-300 overflow-x-auto">
            <pre className="whitespace-pre-wrap">{artifact.content}</pre>
          </div>
        )}
      </div>
    </div>
  );
};
