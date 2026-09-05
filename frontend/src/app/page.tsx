"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/Layout/Header";
import { Sidebar } from "@/components/Layout/Sidebar";
import { ChatPane } from "@/components/Chat/ChatPane";
import { ArtifactViewer } from "@/components/Artifact/ArtifactViewer";
import { useChatStream } from "@/hooks/useChatStream";
import {
  fetchHealth,
  fetchSessions,
  createSession,
  fetchSession,
  deleteSession,
} from "@/lib/api";
import { Session, HealthStatus, Artifact } from "@/lib/types";

export default function Home() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<string>("ollama");
  const [activeArtifact, setActiveArtifact] = useState<Artifact | null>(null);
  const [isArtifactOpen, setIsArtifactOpen] = useState<boolean>(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(false);

  // Streaming Hook
  const {
    messages,
    setMessages,
    isStreaming,
    statusText,
    sendMessage,
    stopStreaming,
  } = useChatStream({
    sessionId: currentSessionId,
    onArtifactReceived: (art) => {
      setActiveArtifact(art);
      setIsArtifactOpen(true);
    },
  });

  // Load initial health diagnostic
  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((err) => console.warn("Initial health check error:", err));

    const timer = setInterval(() => {
      fetchHealth().then(setHealth).catch(() => {});
    }, 30000);
    return () => clearInterval(timer);
  }, []);

  // Load Sessions
  const reloadSessions = useCallback(async () => {
    try {
      const data = await fetchSessions();
      setSessions(data);
      if (data.length > 0 && !currentSessionId) {
        selectSession(data[0].id);
      } else if (data.length === 0) {
        handleNewSession();
      }
    } catch (err) {
      console.warn("Could not fetch sessions from DB:", err);
      // Auto-fallback session
      if (!currentSessionId) {
        handleNewSession();
      }
    }
  }, [currentSessionId]);

  useEffect(() => {
    reloadSessions();
  }, [reloadSessions]);

  const selectSession = async (id: string) => {
    setCurrentSessionId(id);
    try {
      const data = await fetchSession(id);
      setMessages(data.messages || []);
      // Check if any message had artifacts
      const latestArtifact = data.messages
        .flatMap((m) => m.artifacts || [])
        .slice(-1)[0];
      if (latestArtifact) {
        setActiveArtifact(latestArtifact);
      }
    } catch (err) {
      console.warn("Failed to load session messages:", err);
      setMessages([]);
    }
  };

  const handleNewSession = async () => {
    try {
      const newSess = await createSession();
      setSessions((prev) => [newSess, ...prev]);
      setCurrentSessionId(newSess.id);
      setMessages([]);
      setActiveArtifact(null);
      setIsArtifactOpen(false);
    } catch (err) {
      const fallbackId = `sess-${Date.now()}`;
      const fallbackSess: Session = {
        id: fallbackId,
        title: "New Growth Session",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      setSessions((prev) => [fallbackSess, ...prev]);
      setCurrentSessionId(fallbackId);
      setMessages([]);
      setActiveArtifact(null);
      setIsArtifactOpen(false);
    }
  };

  const handleDeleteSession = async (id: string) => {
    try {
      await deleteSession(id);
    } catch (err) {
      console.warn("Delete session API failed, removing locally:", err);
    }
    const filtered = sessions.filter((s) => s.id !== id);
    setSessions(filtered);
    if (currentSessionId === id) {
      if (filtered.length > 0) {
        selectSession(filtered[0].id);
      } else {
        handleNewSession();
      }
    }
  };

  const handleSendMessage = (text: string, mode: "default" | "ship30") => {
    sendMessage(text, mode, selectedProvider);
  };

  const handleOpenArtifact = (art: Artifact) => {
    setActiveArtifact(art);
    setIsArtifactOpen(true);
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-slate-950 overflow-hidden font-sans">
      {/* Top Header */}
      <Header
        health={health}
        selectedProvider={selectedProvider}
        onSelectProvider={setSelectedProvider}
        activeArtifact={activeArtifact}
        isArtifactOpen={isArtifactOpen}
        onToggleArtifact={() => setIsArtifactOpen(!isArtifactOpen)}
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
      />

      {/* Main Workspace Layout */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Collapsible Left Sidebar */}
        <Sidebar
          sessions={sessions}
          currentSessionId={currentSessionId}
          onSelectSession={selectSession}
          onNewSession={handleNewSession}
          onDeleteSession={handleDeleteSession}
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
        />

        {/* Dynamic Dual-Pane Container */}
        <main className="flex-1 flex overflow-hidden relative">
          {/* Left Pane: Chat Workspace */}
          <div
            className={`flex-1 flex flex-col h-full transition-all duration-300 ${
              isArtifactOpen && activeArtifact ? "lg:w-1/2 w-full" : "w-full"
            }`}
          >
            <ChatPane
              messages={messages}
              isStreaming={isStreaming}
              statusText={statusText}
              onSendMessage={handleSendMessage}
              onStopStreaming={stopStreaming}
              onOpenArtifact={handleOpenArtifact}
            />
          </div>

          {/* Right Pane: Claude-Style Artifact Viewer */}
          {isArtifactOpen && activeArtifact && (
            <div className="lg:w-1/2 w-full absolute lg:static inset-0 z-20 h-full flex flex-col shadow-2xl">
              <ArtifactViewer
                artifact={activeArtifact}
                onClose={() => setIsArtifactOpen(false)}
              />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
