export interface SourceCitation {
  episode: string;
  guest: string;
  timestamp: string;
  youtube_url?: string;
  score: number;
  text: string;
}

export interface Artifact {
  id?: string;
  type: "markdown" | "html";
  title: string;
  content: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  sources?: SourceCitation[];
  mode?: "default" | "ship30";
  provider?: string;
  artifacts?: Artifact[];
  created_at?: string;
}

export interface Session {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
}

export interface HealthStatus {
  status: string;
  database: boolean;
  ollama: boolean;
  ollama_model: string;
  total_chunks: number;
  cloud_providers: {
    anthropic: boolean;
    openai: boolean;
  };
  vector_index: boolean;
  retrieval_source: string;
}
