import React from "react";
import { Cpu, Cloud, ChevronDown, Check } from "lucide-react";

interface ModelSelectorProps {
  selectedProvider: string;
  onSelectProvider: (provider: string) => void;
  ollamaAvailable: boolean;
  cloudAvailable: {
    anthropic: boolean;
    openai: boolean;
  };
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  selectedProvider,
  onSelectProvider,
  ollamaAvailable,
  cloudAvailable,
}) => {
  const [isOpen, setIsOpen] = React.useState(false);

  const models = [
    {
      id: "ollama",
      name: "Ollama (llama3.1:8b)",
      type: "local",
      badge: "Local 8B",
      description: "Primary local evaluation model • Zero data leakage",
      available: ollamaAvailable,
    },
    {
      id: "claude",
      name: "Claude 3.5 Sonnet",
      type: "cloud",
      badge: "Anthropic",
      description: "Cloud agent reasoning • High context depth",
      available: cloudAvailable.anthropic,
    },
    {
      id: "openai",
      name: "OpenAI (GPT-4o)",
      type: "cloud",
      badge: "OpenAI",
      description: "Cloud reasoning • Fast multimodal LLM",
      available: cloudAvailable.openai,
    },
  ];

  const currentModel = models.find((m) => m.id === selectedProvider) || models[0];

  return (
    <div className="relative inline-block text-left">
      <button
        onClick={() => setIsOpen(!isOpen)}
        type="button"
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700/80 text-xs font-medium text-slate-200 transition-all shadow-sm"
      >
        {currentModel.type === "local" ? (
          <Cpu className="w-3.5 h-3.5 text-amber-400" />
        ) : (
          <Cloud className="w-3.5 h-3.5 text-sky-400" />
        )}
        <span>{currentModel.name}</span>
        <span
          className={`px-1.5 py-0.2 rounded text-[10px] font-semibold uppercase ${
            currentModel.type === "local"
              ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
              : "bg-sky-500/10 text-sky-400 border border-sky-500/20"
          }`}
        >
          {currentModel.badge}
        </span>
        <ChevronDown className="w-3.5 h-3.5 text-slate-400 ml-0.5" />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-72 rounded-xl bg-slate-900 border border-slate-700/80 shadow-2xl z-50 py-1 overflow-hidden">
            <div className="px-3 py-2 border-b border-slate-800 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Select Inference Provider
            </div>
            {models.map((model) => (
              <button
                key={model.id}
                onClick={() => {
                  onSelectProvider(model.id);
                  setIsOpen(false);
                }}
                className={`w-full text-left px-3 py-2.5 flex items-start gap-2.5 hover:bg-slate-800 transition-colors ${
                  selectedProvider === model.id ? "bg-slate-800/60" : ""
                }`}
              >
                <div className="mt-0.5">
                  {model.type === "local" ? (
                    <Cpu className="w-4 h-4 text-amber-400" />
                  ) : (
                    <Cloud className="w-4 h-4 text-sky-400" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-slate-100">
                      {model.name}
                    </span>
                    {selectedProvider === model.id && (
                      <Check className="w-3.5 h-3.5 text-amber-400" />
                    )}
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5 truncate">
                    {model.description}
                  </p>
                </div>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
};
