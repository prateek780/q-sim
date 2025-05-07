import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { Check, AlertTriangle, Lightbulb } from "lucide-react"
import NetworkVisualizer from "../temp_network_view/network_view"
import { ChatMessageI } from "../message.interface"
import { TopologyGenerationResponse } from "../agent_response"

export function TopologyGeneratorRenderer({ response }: { response:  ChatMessageI<TopologyGenerationResponse>}) {
  const agentMessage = response.agentResponse as TopologyGenerationResponse
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {agentMessage.success ? (
            <Badge className="bg-green-900/30 text-green-400">
              <Check className="h-3 w-3 mr-1" /> Generation Complete
            </Badge>
          ) : (
            <Badge className="bg-red-900/30 text-red-400">
              <AlertTriangle className="h-3 w-3 mr-1" /> Generation Failed
            </Badge>
          )}
          <span className="text-xs text-slate-400">Cost: {agentMessage.cost}</span>
        </div>
      </div>

      {agentMessage.error && (
        <div className="bg-red-900/20 border border-red-900/50 rounded-md p-3 text-sm text-red-400">
          {agentMessage.error}
        </div>
      )}

      {agentMessage.success && (
        <>
          <div className="text-sm">{agentMessage.overall_feedback}</div>

          <Card>
            <CardContent className="p-3">
              <div className="h-[450px] bg-slate-900 rounded-md overflow-hidden w-[900px]">
                <NetworkVisualizer topologyStringifiedData={JSON.stringify(agentMessage.generated_topology)} />
              </div>
            </CardContent>
          </Card>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Lightbulb className="h-4 w-4 text-amber-500" />
              <span>Thought Process</span>
            </div>
            <div className="space-y-2 max-h-[150px] overflow-y-auto pr-2">
              {agentMessage.thought_process.map((thought, index) => (
                <div key={index} className="text-xs bg-slate-800/50 p-2 rounded-md">
                  {index + 1}. {thought}
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
