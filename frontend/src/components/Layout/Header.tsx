import React from "react";
import { Sparkles, Radio, Menu, FileCode2, Database } from "lucide-react";
import { HealthStatus, Artifact } from "@/lib/types";
import { ModelSelector } from "../Chat/ModelSelector";

interface HeaderProps {
  health: HealthStatus | null;
  selectedProvider: string;
  onSelectProvider: (provider: string) => void;
  activeArtifact: Artifact | null;
  isArtifactOpen: boolean;
  onToggleArtifact: () => void;
  onToggleSidebar: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  selectedProvider,
  onSelectProvider,
  activeArtifact,
  isArtifactOpen,
  onToggleArtifact,
  onToggleSidebar,
}) => {
  const isHealthy = health?.status === "healthy";
  const chunksCount = health?.total_chunks || 0;

  return (
    <header className="h-14 border-b border-slate-800 bg-slate-950/80 backdrop-blur px-4 flex items-center justify-between z-10">
      {/* Left Branding */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 lg:hidden"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-amber-500 to-amber-300 flex items-center justify-center text-slate-950 shadow-md shadow-amber-500/10 font-black text-sm">
            L
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-slate-100 tracking-tight">
                The Lenny Growth Assistant
              </span>
              <span className="hidden sm:inline-flex items-center gap-1 text-[10px] font-semibold text-amber-400 bg-amber-500/10 border border-amber-500/20 px-1.5 py-0.2 rounded uppercase">
                RAG Engine
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Right Controls & Indicators */}
      <div className="flex items-center gap-3">
        {/* Chunks & Health Badge */}
        <div className="hidden md:flex items-center gap-2 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-400">
          <div
            className={`w-2 h-2 rounded-full ${
              isHealthy ? "bg-emerald-400 shadow-sm shadow-emerald-400/50" : "bg-amber-400"
            }`}
          />
          <span className="text-[11px]">
            {chunksCount} chunks indexed
          </span>
        </div>

        {/* Model Provider Selector */}
        <ModelSelector
          selectedProvider={selectedProvider}
          onSelectProvider={onSelectProvider}
          ollamaAvailable={health?.ollama ?? true}
          cloudAvailable={health?.cloud_providers ?? { anthropic: false, openai: false }}
        />

        {/* Artifact Drawer Toggle */}
        {activeArtifact && (
          <button
            onClick={onToggleArtifact}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
              isArtifactOpen
                ? "bg-amber-500 text-slate-950 border-amber-400 font-semibold"
                : "bg-slate-800 hover:bg-slate-700 text-amber-400 border-amber-500/30"
            }`}
          >
            <FileCode2 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">
              {isArtifactOpen ? "Hide Artifact" : "View Artifact"}
            </span>
          </button>
        )}
      </div>
    </header>
  );
};
