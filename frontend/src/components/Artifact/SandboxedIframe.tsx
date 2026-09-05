import React, { useMemo } from "react";
import DOMPurify from "dompurify";
import { ShieldCheck } from "lucide-react";

interface SandboxedIframeProps {
  content: string;
  title: string;
}

export const SandboxedIframe: React.FC<SandboxedIframeProps> = ({ content, title }) => {
  // Sanitize markup prior to injecting into iframe srcDoc
  const cleanHtml = useMemo(() => {
    if (typeof window === "undefined") return content;
    return DOMPurify.sanitize(content, {
      WHOLE_DOCUMENT: true,
      ADD_TAGS: ["style", "link", "script"],
      ADD_ATTR: ["target"],
    });
  }, [content]);

  return (
    <div className="flex flex-col h-full w-full border border-slate-700/60 rounded-lg overflow-hidden bg-white shadow-md">
      <div className="bg-slate-100 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 px-3 py-2 flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-700 dark:text-slate-200 tracking-wide uppercase truncate max-w-xs">
          Interactive HTML: {title}
        </span>
        <div className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50 px-2 py-0.5 rounded border border-emerald-200 dark:border-emerald-800 text-[11px] font-medium">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Sandboxed (`sandbox="allow-scripts"`)</span>
        </div>
      </div>
      <iframe
        title={title}
        srcDoc={cleanHtml}
        // Strict security isolation: allow scripts to run for interactivity,
        // but omit allow-same-origin to prevent access to parent cookies, local storage, and DOM.
        sandbox="allow-scripts"
        className="w-full h-full border-none min-h-[450px]"
      />
    </div>
  );
};
