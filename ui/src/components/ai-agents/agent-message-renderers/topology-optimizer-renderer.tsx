import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Check, Info, PlusCircle, MinusCircle, ArrowRightLeft } from "lucide-react"
import NetworkVisualizer from "../temp_network_view/network_view"
import { ChatMessageI } from "../message.interface"
import { TopologyOptimizerResponse } from "../agent_response"

export function TopologyOptimizerRenderer({ response }: { response: ChatMessageI<TopologyOptimizerResponse> }) {
  const agentMessage = response.agentResponse as TopologyOptimizerResponse


  if(!agentMessage) {
    return null
  }

  // Helper function to get icon for change type
  const getChangeIcon = (change: string) => {
    if (change.includes("add")) return <PlusCircle className="h-4 w-4 text-green-500" />
    if (change.includes("remove")) return <MinusCircle className="h-4 w-4 text-red-500" />
    if (change.includes("modify") || change.includes("change"))
      return <ArrowRightLeft className="h-4 w-4 text-blue-500" />
    return <Info className="h-4 w-4 text-slate-400" />
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Badge className="bg-green-900/30 text-green-400">
            <Check className="h-3 w-3 mr-1" /> Optimization Complete
          </Badge>
          <span className="text-xs text-slate-400">Cost: {agentMessage.cost}</span>
        </div>
      </div>

      <Tabs defaultValue="summary">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="summary">Summary</TabsTrigger>
          <TabsTrigger value="comparison">Comparison</TabsTrigger>
          <TabsTrigger value="steps">Optimization Steps</TabsTrigger>
        </TabsList>

        <TabsContent value="summary" className="space-y-4 pt-4">
          <div className="text-sm">{agentMessage.overall_feedback}</div>
        </TabsContent>

        <TabsContent value="comparison" className="pt-4">
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <CardHeader className="py-2 px-4">
                <CardTitle className="text-sm">Original Topology</CardTitle>
              </CardHeader>
              <CardContent className="p-2">
                <div className="h-[500px] bg-slate-900 rounded-md overflow-hidden w-[600px]">
                  <NetworkVisualizer topologyStringifiedData={JSON.stringify(agentMessage.original_topology)} />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="py-2 px-4">
                <CardTitle className="text-sm">Optimized Topology</CardTitle>
              </CardHeader>
              <CardContent className="p-2">
                <div className="h-[500px] bg-slate-900 rounded-md overflow-hidden w-[600px]">
                  <NetworkVisualizer topologyStringifiedData={JSON.stringify(agentMessage.optimized_topology)} />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="steps" className="pt-4">
          <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2">
            {agentMessage.optimization_steps.map((step, index) => (
              <Card key={index}>
                <CardContent className="p-3">
                  <div className="flex items-start gap-2">
                    {getChangeIcon(step.change)}
                    <div className="flex-1">
                      <div className="font-medium text-sm">{step.change}</div>
                      <div className="text-xs text-slate-400 mt-1">Path: {step.change_path.join(" → ")}</div>
                      <Separator className="my-2" />
                      <div className="text-xs">{step.reason}</div>
                      {step.comments && <div className="text-xs italic text-slate-400 mt-1">{step.comments}</div>}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
