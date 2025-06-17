import { TopologyOptimizerRenderer } from "./topology-optimizer-renderer"
import { TopologyGeneratorRenderer } from "./topology-generator-renderer"
import { LogSummaryRenderer } from "./log-summary-renderer"
import { OrchestratorRenderer } from "./orchestrator-renderer"
import { ChatMessageI } from "../message.interface"
import { AgentI, AgentID, AgentTask } from "../agent-declaration"
import { LogSummaryResponse, OrchestratorResponse, TopologyGenerationResponse, TopologyOptimizerResponse } from "../agent_response"

interface MessageRendererProps {
  message: ChatMessageI
  agents: AgentI[]
}


export function MessageContentRenderer({ message, agents }: MessageRendererProps) {
  // Determine the message type based on content structure and agent
  const getMessageType = (): (AgentTask | string) => {
    if (!message || !message.content) return "text"

    // Check for specific agent response types
    if (message.agentId === AgentID.TOPOLOGY_DESIGNER) {
      if (message.taskId === AgentTask.TOPOLOGY_QNA) return 'text'
      if (message.taskId)
        return message.taskId
    }

    if (message.agentId === AgentID.LOG_SUMMARIZER && message.taskId) {
      if (message.taskId === AgentTask.LOG_QNA) return 'text'

      return message.taskId
    }

    if (message.agentId === AgentID.ORCHESTRATOR) return "orchestrator"

    // Default to text if no specific type is detected
    return "text"
  }

  const messageType = getMessageType()

  // Render the appropriate component based on message type
  switch (messageType) {
    case AgentTask.OPTIMIZE_TOPOLOGY:
      return <TopologyOptimizerRenderer response={message as ChatMessageI<TopologyOptimizerResponse>} />

    case AgentTask.SYNTHESIZE_TOPOLOGY:
      return <TopologyGeneratorRenderer response={message as ChatMessageI<TopologyGenerationResponse>} />

    case AgentTask.LOG_SUMMARIZATION:
      return <LogSummaryRenderer response={message as ChatMessageI<LogSummaryResponse>} />

    case "orchestrator":
      return <OrchestratorRenderer response={message as ChatMessageI<OrchestratorResponse>} agents={agents} />

    case "text":
    default:
      // For text messages, render the content as is
      return (
        <div className="text-sm whitespace-pre-wrap">
          {typeof message.content === "string"
            ? message.content.split(/(@[A-Za-z\s-]+)/).map((part: string, index: number) => {
              // Check if this part is a mention
              const mentionMatch = part.match(/@([A-Za-z\s-]+)/)
              if (mentionMatch) {
                const mentionedName = mentionMatch[1].trim()
                const mentionedAgent = agents.find((a: any) => a.name.toLowerCase() === mentionedName.toLowerCase())

                if (mentionedAgent) {
                  return (
                    <span key={index} className={`font-medium ${mentionedAgent.textColor}`}>
                      {part}
                    </span>
                  )
                }
              }
              return <span key={index} dangerouslySetInnerHTML={{ __html: part }}></span>
            })
            : JSON.stringify(message.content)}
        </div>
      )
  }
}
