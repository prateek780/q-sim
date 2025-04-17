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
