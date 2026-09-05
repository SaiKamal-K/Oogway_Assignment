import React from "react";
import { Plus, MessageSquare, Trash2, Headphones, ExternalLink } from "lucide-react";
import { Session } from "@/lib/types";

interface SidebarProps {
  sessions: Session[];
  currentSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewSession: () => void;
  onDeleteSession: (id: string) => void;
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  currentSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  isOpen,
  onClose,
}) => {
  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-30 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed lg:static top-0 bottom-0 left-0 w-64 bg-slate-950 border-r border-slate-800 flex flex-col z-40 transition-transform duration-200 ${
          isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        }`}
      >
        {/* Top Action */}
        <div className="p-3 border-b border-slate-800/80">
          <button
            onClick={() => {
              onNewSession();
              onClose();
            }}
            className="w-full flex items-center justify-center gap-2 px-3.5 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-400 hover:from-amber-400 hover:to-amber-300 text-slate-950 text-xs font-bold shadow-md shadow-amber-500/10 transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>New Growth Session</span>
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          <div className="px-2.5 py-1.5 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
            Recent Conversations
          </div>

          {sessions.length === 0 ? (
            <div className="px-3 py-6 text-center text-xs text-slate-500">
              No previous chats yet. Start asking questions above!
            </div>
          ) : (
            sessions.map((sess) => {
              const isSelected = sess.id === currentSessionId;
              return (
                <div
                  key={sess.id}
                  onClick={() => {
                    onSelectSession(sess.id);
                    onClose();
                  }}
                  className={`group relative flex items-center justify-between px-3 py-2 rounded-lg text-xs cursor-pointer transition-colors ${
                    isSelected
                      ? "bg-slate-800/90 text-amber-400 font-medium border border-slate-700/60"
                      : "text-slate-300 hover:bg-slate-900 hover:text-slate-100"
                  }`}
                >
                  <div className="flex items-center gap-2 min-w-0 pr-2">
                    <MessageSquare className="w-3.5 h-3.5 flex-shrink-0 text-slate-500 group-hover:text-slate-300" />
                    <span className="truncate">{sess.title}</span>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteSession(sess.id);
                    }}
                    title="Delete session"
                    className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-500/20 text-slate-500 hover:text-red-400 transition-all"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-slate-800/80 bg-slate-950/60 text-xs text-slate-400 space-y-2">
          <a
            href="https://www.lennysnewsletter.com/podcast"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-900 text-slate-400 hover:text-amber-400 transition-colors"
          >
            <Headphones className="w-4 h-4 text-amber-500" />
            <span className="text-[11px] font-medium flex-1">
              Lenny's Podcast Archive
            </span>
            <ExternalLink className="w-3 h-3 text-slate-500" />
          </a>
        </div>
      </aside>
    </>
  );
};
