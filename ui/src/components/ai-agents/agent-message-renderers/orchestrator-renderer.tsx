import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { Bot, ArrowRight, Lightbulb } from "lucide-react"
import { ChatMessageI } from "../message.interface"
import { OrchestratorResponse } from "../agent_response";


export function OrchestratorRenderer({ response, agents }: { response: ChatMessageI<OrchestratorResponse>; agents: any[] }) {
  const agentMessage = response.agentResponse as OrchestratorResponse
  // Find the delegated agent
  const delegatedAgent = agents.find((a) => a.id === agentMessage.agent_id)

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Badge className="bg-purple-900/30 text-purple-400">
          <Bot className="h-3 w-3 mr-1" /> Orchestration
        </Badge>
        <span className="text-xs text-slate-400">Task ID: {agentMessage.task_id}</span>
      </div>

      <div className="flex items-center gap-2 text-sm">
        <Lightbulb className="h-4 w-4 text-amber-500" />
        <div className="font-medium">Reasoning</div>
      </div>
      <div className="text-sm bg-slate-800/50 p-3 rounded-md">{agentMessage.reason}</div>

      {delegatedAgent && (
        <div className="flex items-center gap-2">
          <div className="text-sm">Delegated to:</div>
          <div className="flex items-center gap-2">
            <div className={`w-5 h-5 rounded-full flex items-center justify-center ${delegatedAgent.color}`}>
              {delegatedAgent.icon}
            </div>
            <span className={`text-sm font-medium ${delegatedAgent.textColor}`}>{delegatedAgent.name}</span>
          </div>
          <ArrowRight className="h-4 w-4 text-slate-400" />
        </div>
      )}

      {agentMessage.suggestion && (
        <Card>
          <CardContent className="p-3">
            <div className="text-sm font-medium mb-1">Suggestion</div>
            <div className="text-xs">{agentMessage.suggestion}</div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
