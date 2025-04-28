"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
    Bot,
    Send,
    RefreshCw,
    Download,
    Info,
    Loader2,
} from "lucide-react"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { AGENT_DEFINITION, AgentID } from "./agent-declaration"
import { DUMMY_CHAT } from "./dummy-chat"
import { Message } from "./message"
import { ChatMessageI, ChatRequestI } from "./message.interface"
import api from "@/services/api"
import { LogSummaryResponse, OrchestratorResponse } from "./agent_response"
import { getLogger } from "@/helpers/simLogger"

// Agent types and their details
const agentTypes = AGENT_DEFINITION;

// Sample conversation history for demo purposes, will be handled by state eventually.
const initialConversation = DUMMY_CHAT;

// Unified agent chat component
export function AIAgentsPanel() {
    const [messages, setMessages] = useState<ChatMessageI[]>([])
    const [inputValue, setInputValue] = useState("")
    const [activeAgents, setActiveAgents] = useState(agentTypes.map((agent) => agent.id))
    const [currentTab, setCurrentTab] = useState("chat")
    const [agentInProgress, setAgentInProgress] = useState<boolean>(false);
    const messagesEndRef = useRef<HTMLDivElement>(null)
    const logger = getLogger("AIAgentsPanel")

    // Scroll to bottom when messages change
    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: "smooth" })
        }
    }, [messages])

    // Toggle agent active state
    const toggleAgentActive = (agentId: AgentID) => {
        if (activeAgents.includes(agentId)) {
            setActiveAgents(activeAgents.filter((id) => id !== agentId))
        } else {
            setActiveAgents([...activeAgents, agentId])
        }
    }

    // Extract @mentions from message
    const extractMention = (message: string): { mentionedAgentId: AgentID, cleanMessage: string } => {
        // Create a regex pattern dynamically from agent names
        const agentNames = agentTypes.map(a => a.name.replace(/[-\s]/g, '[-\\s]+')).join('|');
        const mentionRegex = new RegExp(`@(${agentNames})\\b`, 'i');

        const match = message.match(mentionRegex);

        if (match) {
            const mentionedName = match[1].trim();
            const mentionedAgent = agentTypes.find(a =>
                a.name.toLowerCase() === mentionedName.toLowerCase());

            // Remove the mention part from the message
            const cleanMessage = message.replace(match[0], '').trim();
            if (mentionedAgent) {
                return {
                    mentionedAgentId: mentionedAgent.id,
                    cleanMessage
                };
            }
        }

        return {
            mentionedAgentId: AgentID.ORCHESTRATOR,
            cleanMessage: message
        };
    }

    const handleTopologyDesignerMessage = (message: string) => {
        const responseContent =
            "I've analyzed the network topology and created an optimized design that reduces potential congestion points by 35%. The new topology maintains all required connectivity while improving path diversity."
        const attachments = [
            {
                type: "json",
                name: "optimized_topology.json",
                preview: '{"nodes": 8, "connections": 12, "congestion_reduction": "35%"}',
            },
            {
                type: "image",
                name: "topology_visualization.png",
                preview: "Visual representation of the optimized network topology",
            },
        ]

        return { responseContent, attachments }
    }

    const handleCongestionMonitorMessage = (message: string) => {
        const responseContent =
            "Monitoring active... I've detected moderate congestion in the quantum channel between nodes QuantumHost1 and QuantumAdapter. Current buffer utilization is at 72% with increasing trend. Recommend traffic redistribution within the next 5 minutes."

        const attachments = [
            {
                type: "json",
                name: "congestion_alert.json",
                preview: '{"severity": "moderate", "location": "QuantumHost1->QuantumAdapter", "utilization": 0.72}',
            },
        ]
        return { responseContent, attachments }
    }


    const handlePerformanceAnalyzerMessage = (message: string) => {
        const responseContent =
            "Performance analysis complete. Current network efficiency rating: 76/100. Key bottlenecks identified in quantum memory allocation and entanglement distribution. Implementing recommended optimizations could improve overall efficiency by 22%."
        const attachments = [
            {
                type: "csv",
                name: "performance_metrics.csv",
                preview: "Metric,Value,Benchmark\nLatency,12.3ms,<10ms\nThroughput,24.5 qubits/s,>30 qubits/s",
            },
        ]
        return { responseContent, attachments }

    }

    const handleCompoundAIArchitectMessage = (message: string) => {
        const responseContent =
            "Orchestrating multi-agent analysis... I've coordinated with all available agents to develop a comprehensive optimization strategy. The plan includes topology adjustments, congestion prevention measures, and performance tuning in a 3-phase implementation."
        const attachments = [
            {
                type: "json",
                name: "optimization_plan.json",
                preview: '{"phases": 3, "estimated_improvement": "28%", "risk_level": "low"}',
            },
        ]
        return { responseContent, attachments }
    }

    const handleOrchestratorResponse = (message: OrchestratorResponse): ChatMessageI | null => {
        if (!message.agent_id) {
            // Could not find relevant agent
            return {
                content: message.suggestion,
                role: 'agent',
                id: (messages.length + 1).toString(),
                timestamp: new Date().toISOString(),
                agentId: AgentID.ORCHESTRATOR,
            }
        } else if (message.agent_response) {
            handleReceivedMessage(message.agent_id as AgentID, message.agent_response)
        } else {
            logger.error("Orchestrator response does not contain agent response")
        }
        return null

    }

    const handleLogSummarizerMessage = (message: LogSummaryResponse): ChatMessageI => {
        const responseContent = message.short_summary;
        return {
            content: responseContent,
            role: 'agent',
            id: (messages.length + 1).toString(),
            timestamp: new Date().toISOString(),
            agentId: AgentID.LOG_SUMMARIZER,
        }
    }

    const handleReceivedMessage = async (agentId: AgentID, response: any) => {
        var responseMessage: ChatMessageI | null = null;
        switch (agentId) {
            case AgentID.LOG_SUMMARIZER:
                responseMessage = handleLogSummarizerMessage(response);
                break;

            case AgentID.ORCHESTRATOR:
                responseMessage = handleOrchestratorResponse(response);
                break;

            default:
                console.log("Unknown agent ID:", agentId);
                break;
        }

        if (responseMessage) {
            setMessages([...messages, responseMessage]);
        }
    }

    const sendAgentChatMessage = async (agentId: AgentID, content: string, attachments: any[] = []) => {
        const chatRequest: ChatRequestI = {
            agent_id: agentId,
            user_query: content,
        };

        const response = await api.sendAgentMessage(chatRequest)

        await handleReceivedMessage(agentId, response);
    };

    // Handle sending a message
    const handleSendMessage = async () => {
        if (!inputValue.trim()) return

        try {
            setAgentInProgress(true);
            // Extract mentioned agent
            const { mentionedAgentId, cleanMessage } = extractMention(inputValue);

            if (mentionedAgentId && (activeAgents.includes(mentionedAgentId) || mentionedAgentId === AgentID.ORCHESTRATOR)) {
                await sendAgentChatMessage(mentionedAgentId, cleanMessage);
            }
            setAgentInProgress(false);
        } catch (error) {
            console.error("Error sending message:", error);
            setAgentInProgress(false);
        }
    }

    // Handle input keydown (for Enter key)
    const handleKeyDown = (e: any) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault()
            handleSendMessage()
        }
    }

    // Render agent mention suggestions
    const renderMentionSuggestions = () => {
        if (!inputValue.includes("@")) return null

        const lastMentionIndex = inputValue.lastIndexOf("@")
        const partialMention = inputValue
            .slice(lastMentionIndex + 1)
            .split(/\s/)[0]
            .toLowerCase()

        if (!partialMention) return null

        const matchingAgents = agentTypes.filter(
            (agent) => agent.name.toLowerCase().includes(partialMention) && activeAgents.includes(agent.id),
        )

        if (matchingAgents.length === 0) return null

        return (
            <div className="absolute bottom-full mb-2 bg-slate-800 border border-slate-700 rounded-md overflow-hidden shadow-lg">
                {matchingAgents.map((agent) => (
                    <button
                        key={agent.id}
                        className="flex items-center gap-2 w-full p-2 hover:bg-slate-700 text-left"
                        onClick={() => {
                            // Replace the partial @mention with the full agent name
                            const newInput =
                                inputValue.slice(0, lastMentionIndex) +
                                `@${agent.name}` +
                                inputValue.slice(lastMentionIndex + partialMention.length + 1)
                            setInputValue(newInput)
                        }}
                    >
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center ${agent.color}`}>{agent.icon}</div>
                        <span>{agent.name}</span>
                    </button>
                ))}
            </div>
        )
    }

    return (
        <div className="h-full flex flex-col">
            <Tabs value={currentTab} onValueChange={setCurrentTab} className="flex-1 flex flex-col">
                <div className="flex items-center justify-between p-3 border-b border-slate-700">
                    <TabsList className="bg-slate-800">
                        <TabsTrigger value="chat" className="data-[state=active]:bg-slate-700">
                            Chat
                        </TabsTrigger>
                        <TabsTrigger value="agents" className="data-[state=active]:bg-slate-700">
                            Agents
                        </TabsTrigger>
                        <TabsTrigger value="settings" className="data-[state=active]:bg-slate-700">
                            Settings
                        </TabsTrigger>
                    </TabsList>

                    <div className="flex items-center gap-2">
                        <TooltipProvider>
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <Button variant="outline" size="icon" className="h-8 w-8">
                                        <RefreshCw className="h-4 w-4" />
                                    </Button>
                                </TooltipTrigger>
                                <TooltipContent>
                                    <p>Reset conversation</p>
                                </TooltipContent>
                            </Tooltip>
                        </TooltipProvider>

                        <TooltipProvider>
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <Button variant="outline" size="icon" className="h-8 w-8">
                                        <Download className="h-4 w-4" />
                                    </Button>
                                </TooltipTrigger>
                                <TooltipContent>
                                    <p>Export conversation</p>
                                </TooltipContent>
                            </Tooltip>
                        </TooltipProvider>
                    </div>
                </div>

                <TabsContent value="chat" className="flex-1 flex flex-col p-0 m-0 max-h-[900px]">
                    <ScrollArea className="flex-1 p-4  overflow-y-auto">
                        <div className="space-y-4">
                            {messages.map((message, idx) => (
                                <Message key={message.id + '__' + idx} message={message} agents={agentTypes} />
                            ))}
                            <div ref={messagesEndRef} />
                        </div>
                    </ScrollArea>

                    <div className="p-3 border-t border-slate-700">
                        <div className="flex items-center gap-2 relative">
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                    <Button variant="outline" size="icon" className="h-10 w-10 flex-shrink-0">
                                        <Bot className="h-5 w-5" />
                                    </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="start">
                                    {agentTypes.map((agent) => (
                                        <DropdownMenuItem
                                            key={agent.id}
                                            disabled={!activeAgents.includes(agent.id)}
                                            onClick={() => setInputValue(`@${agent.name} `)}
                                        >
                                            <div className="flex items-center gap-2">
                                                <div className={`w-5 h-5 rounded-full flex items-center justify-center ${agent.color}`}>
                                                    {agent.icon}
                                                </div>
                                                <span>@{agent.name}</span>
                                            </div>
                                        </DropdownMenuItem>
                                    ))}
                                </DropdownMenuContent>
                            </DropdownMenu>

                            <div className="relative flex-1">
                                {renderMentionSuggestions()}
                                <Input
                                    placeholder="Type a message... (Use @AgentName to mention a specific agent)"
                                    value={inputValue}
                                    onChange={(e) => setInputValue(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                    className="pr-10"
                                />
                                <div className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-slate-400">
                                    {activeAgents.length}/{agentTypes.length}
                                </div>
                            </div>

                            <Button onClick={handleSendMessage} className="flex-shrink-0">
                                {agentInProgress ? <Loader2 className="animate-spin" /> : <Send className="h-4 w-4 mr-2" />
                                }
                            </Button>
                        </div>
                    </div>
                </TabsContent>

                <TabsContent value="agents" className="flex-1 p-4 m-0 overflow-auto">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {agentTypes.map((agent) => (
                            <Card key={agent.id} className={`border-l-4 ${agent.borderColor}`}>
                                <CardHeader className="p-4 pb-2">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <div className={`p-1.5 rounded-md ${agent.color}`}>{agent.icon}</div>
                                            <CardTitle className="text-base">{agent.name}</CardTitle>
                                        </div>
                                        <Switch
                                            checked={activeAgents.includes(agent.id)}
                                            onCheckedChange={() => toggleAgentActive(agent.id)}
                                        />
                                    </div>
                                </CardHeader>
                                <CardContent className="p-4 pt-2">
                                    <p className="text-sm text-slate-400 mb-3">{agent.description}</p>

                                    <div className="space-y-3">
                                        <div>
                                            <h4 className="text-xs font-medium text-slate-500 mb-1">INPUTS</h4>
                                            <ul className="text-xs space-y-1">
                                                {agent.inputs.map((input, index) => (
                                                    <li key={index} className="flex items-start gap-1">
                                                        <Info className="h-3 w-3 text-slate-500 mt-0.5" />
                                                        <span>{input}</span>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>

                                        <div>
                                            <h4 className="text-xs font-medium text-slate-500 mb-1">OUTPUTS</h4>
                                            <ul className="text-xs space-y-1">
                                                {agent.outputs.map((output, index) => (
                                                    <li key={index} className="flex items-start gap-1">
                                                        <Info className="h-3 w-3 text-slate-500 mt-0.5" />
                                                        <span>{output}</span>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </TabsContent>

                <TabsContent value="settings" className="p-4 m-0">
                    <div className="space-y-6">
                        <div>
                            <h3 className="text-lg font-medium mb-4">Agent Settings</h3>
                            <div className="space-y-4">
                                {agentTypes.map((agent) => (
                                    <div key={agent.id} className="flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                            <div className={`p-1.5 rounded-md ${agent.color}`}>{agent.icon}</div>
                                            <div>
                                                <div className="font-medium">{agent.name}</div>
                                                <div className="text-sm text-slate-400">
                                                    {agent.type === "active" ? "Active" : "Passive"} agent
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-4">
                                            <div className="flex items-center space-x-2">
                                                <Label htmlFor={`activate-${agent.id}`} className="text-sm">
                                                    Active
                                                </Label>
                                                <Switch
                                                    id={`activate-${agent.id}`}
                                                    checked={activeAgents.includes(agent.id)}
                                                    onCheckedChange={() => toggleAgentActive(agent.id)}
                                                />
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <Separator />

                        <div>
                            <h3 className="text-lg font-medium mb-4">Interface Settings</h3>
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <div className="font-medium">Auto-complete @mentions</div>
                                        <div className="text-sm text-slate-400">Show suggestions when typing @ symbol</div>
                                    </div>
                                    <Switch defaultChecked />
                                </div>

                                <div className="flex items-center justify-between">
                                    <div>
                                        <div className="font-medium">Show agent icons</div>
                                        <div className="text-sm text-slate-400">Display agent icons in messages</div>
                                    </div>
                                    <Switch defaultChecked />
                                </div>

                                <div className="flex items-center justify-between">
                                    <div>
                                        <div className="font-medium">Compact view</div>
                                        <div className="text-sm text-slate-400">Use less space for messages</div>
                                    </div>
                                    <Switch />
                                </div>
                            </div>
                        </div>
                    </div>
                </TabsContent>
            </Tabs>
        </div>
    )
}
