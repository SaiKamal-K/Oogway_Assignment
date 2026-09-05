import { HealthStatus, Session, Message } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}

export async function fetchSessions(): Promise<Session[]> {
  const res = await fetch(`${API_BASE}/api/sessions`);
  if (!res.ok) throw new Error("Failed to fetch sessions");
  return res.json();
}

export async function createSession(title?: string): Promise<Session> {
  const res = await fetch(`${API_BASE}/api/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: title || "New Growth Session" }),
  });
  if (!res.ok) throw new Error("Failed to create session");
  return res.json();
}

export async function fetchSession(sessionId: string): Promise<{ id: string; title: string; messages: Message[] }> {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`);
  if (!res.ok) throw new Error("Failed to fetch session detail");
  return res.json();
}

export async function deleteSession(sessionId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete session");
}
