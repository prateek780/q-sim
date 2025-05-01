import { AgentID, AgentTask } from "./agent-declaration";

export interface ChatAttachmentI {
    type: string;
    name: string;
    preview: string;
}

export interface ChatMessageI {
    id: string;
    role: "system" | "user" | "agent";
    content: string;
    timestamp: string;
    mentionedAgent?: string;
    agentId?: string;
    referencedAgents?: string[];
    attachments?: ChatAttachmentI[];
}

export interface ChatRequestI {
    agent_id: AgentID;
    task_id?: AgentTask;
    user_query: string;
    tags?: string[];
}

export interface LogAgentRequest extends ChatRequestI {
    simulation_id: string;
}

export interface TopologyOptimizerRequest extends ChatRequestI {
    world_id: string;
    optional_instructions?: string;
}

export interface TopologyGenerationRequest extends ChatRequestI {
}

export interface AgentRouterRequest extends ChatRequestI {
    extra_kwargs: any
}