import type { AgentType } from "@/types/chat";

const config: Record<AgentType, { label: string; className: string }> = {
  research: { label: "Research", className: "bg-blue-500/20 text-blue-300 border-blue-500/30" },
  writing: { label: "Writing", className: "bg-purple-500/20 text-purple-300 border-purple-500/30" },
  tasks: { label: "Tasks", className: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30" },
  clarify: { label: "Clarify", className: "bg-gray-500/20 text-gray-300 border-gray-500/30" },
};

export default function AgentBadge({ agent }: { agent: AgentType }) {
  const { label, className } = config[agent] ?? config.clarify;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${className}`}>
      {label}
    </span>
  );
}
