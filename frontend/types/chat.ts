export type AgentType = "research" | "writing" | "tasks" | "clarify";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent?: AgentType;
  timestamp: Date;
}

export interface ChatResponse {
  reply: string;
  agent: AgentType;
  input_tokens: number;
  output_tokens: number;
}
