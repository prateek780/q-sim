import { ChatMessageI } from './message.interface';

export const DUMMY_CHAT: ChatMessageI[] = [
    {
        id: "system-1",
        role: "system",
        content: "AI Agent System initialized. You can interact with any agent using @mentions.",
        timestamp: "10:30:15",
    },
    {
        id: "user-1",
        role: "user",
        content: "@Congestion Monitor, analyze the current network for potential congestion points.",
        timestamp: "10:31:22",
        mentionedAgent: "congestion-monitor",
    },
    {
        id: "agent-1",
        role: "agent",
        agentId: "congestion-monitor",
        content:
            "Analyzing network for congestion... I've detected potential congestion points at the quantum channel between QuantumHost1 and QuantumAdapter. Current FLIT buffer utilization is at 78%, approaching the 85% warning threshold.",
        timestamp: "10:31:45",
        attachments: [
            {
                type: "json",
                name: "congestion_analysis.json",
                preview: '{"timestamp": "10:31:45", "hotspots": [{"node": "QuantumAdapter", "utilization": 0.78}]}',
            },
            {
                type: "image",
                name: "network_heatmap.png",
                preview: "Network congestion heatmap visualization",
            },
        ],
    },
    {
        id: "user-2",
        role: "user",
        content: "@Topology Designer, suggest an optimized topology to prevent the congestion identified above.",
        timestamp: "10:32:30",
        mentionedAgent: "topology-designer",
    },
    {
        id: "agent-2",
        role: "agent",
        agentId: "topology-designer",
        content:
            "Based on the congestion analysis from @Congestion Monitor, I recommend redistributing the quantum channel load by adding a secondary path between QuantumHost1 and QuantumHost2. This will reduce the load on the QuantumAdapter by approximately 40%.",
        timestamp: "10:32:55",
        referencedAgents: ["congestion-monitor"],
        attachments: [
            {
                type: "json",
                name: "topology_recommendation.json",
                preview: '{"recommendation": "add_channel", "source": "QuantumHost1", "target": "QuantumHost2"}',
            },
        ],
    },
    {
        id: "agent-3",
        role: "agent",
        agentId: "performance-analyzer",
        content:
            "I've analyzed the topology recommendation. The proposed changes would improve overall network efficiency by approximately 23% and reduce the maximum congestion probability from 0.31 to 0.12.",
        timestamp: "10:33:20",
        referencedAgents: ["topology-designer"],
    },
    {
        id: "user-3",
        role: "user",
        content:
            "@Compound AI Architect, can you create a comprehensive plan to implement these recommendations and optimize the entire network?",
        timestamp: "10:34:15",
        mentionedAgent: "compound-ai-architect",
    },
    {
        id: "agent-4",
        role: "agent",
        agentId: "compound-ai-architect",
        content:
            "I'll orchestrate a comprehensive optimization plan based on inputs from all agents. Generating a multi-phase implementation strategy that prioritizes the critical congestion points while maintaining network availability during transitions.",
        timestamp: "10:34:45",
        referencedAgents: ["congestion-monitor", "topology-designer", "performance-analyzer"],
        attachments: [
            {
                type: "csv",
                name: "implementation_schedule.csv",
                preview: "Phase,Action,Expected Impact,Duration\n1,Add secondary quantum channel,40% congestion reduction,5min",
            },
            {
                type: "json",
                name: "deployment_plan.json",
                preview:
                    '{"phases": 3, "estimated_completion_time": "10:45:00", "expected_improvement": "31% overall efficiency"}',
            },
        ],
    },
]
