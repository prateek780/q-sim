import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  FileText,
  AlertTriangle,
  Info,
  CheckCircle,
  Network,
  ArrowRight,
  ChevronDown,
  ChevronRight,
  BarChart2,
 } from "lucide-react"
import { ChatMessageI } from "../message.interface"
import { LogSummaryResponse } from "../agent_response"
import { Progress } from "@radix-ui/react-progress"
import { Separator } from "@radix-ui/react-separator"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { useState } from "react"


export function LogSummaryRenderer({ response }: { response: ChatMessageI<LogSummaryResponse> }) {
  const [expandedFlowIndex, setExpandedFlowIndex] = useState<number | null>(null)
  const [expandedIssueIndex, setExpandedIssueIndex] = useState<number | null>(null)
  
  const agentResponse = response.agentResponse
  if (!agentResponse) {
    return null
  }
  // Calculate percentages for source and destination charts
  const calculatePercentage = (count: number) => {
    return Math.round((count / agentResponse.detailed_summary.total_packets_transmitted) * 100)
  }

  // Sort sources and destinations by packet count (descending)
  const sortedSources = Object.entries(agentResponse.detailed_summary.packets_by_source).sort((a, b) => b[1] - a[1])
  const sortedDestinations = Object.entries(agentResponse.detailed_summary.packets_by_destination).sort(
    (a, b) => b[1] - a[1],
  )

  // Get top 5 sources and destinations
  const topSources = sortedSources.slice(0, 5)
  const topDestinations = sortedDestinations.slice(0, 5)

  // Sort communication flows by packet count (descending)
  const sortedFlows = [...agentResponse.detailed_summary.communication_flows].sort((a, b) => b.packet_count - a.packet_count)

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "error":
      case "critical":
      case "high":
        return <AlertTriangle className="h-4 w-4 text-red-500" />
      case "warning":
      case "medium":
        return <AlertTriangle className="h-4 w-4 text-amber-500" />
      case "success":
        return <CheckCircle className="h-4 w-4 text-green-500" />
      default:
        return <Info className="h-4 w-4 text-blue-500" />
    }
  }

  const getSeverityClass = (severity: string) => {
    switch (severity) {
      case "error":
      case "critical":
      case "high":
        return "border-l-red-500"
      case "warning":
      case "medium":
        return "border-l-amber-500"
      case "success":
        return "border-l-green-500"
      default:
        return "border-l-blue-500"
    }
  }

  return (
    <div className="space-y-3">
      {/* Header with summary stats - more compact layout */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Badge className="bg-blue-900/30 text-blue-400">
            <FileText className="h-3 w-3 mr-1" /> Log Summary
          </Badge>
          <span className="text-xs text-slate-400">
            {agentResponse.summary_period.start} - {agentResponse.summary_period.end}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Badge className="bg-blue-900/30 text-blue-400">
            <BarChart2 className="h-3 w-3 mr-1" /> {agentResponse.detailed_summary.total_packets_transmitted} packets
          </Badge>

          {agentResponse.detailed_summary.errors_found > 0 && (
            <Badge className="bg-red-900/30 text-red-400">
              <AlertTriangle className="h-3 w-3 mr-1" /> {agentResponse.detailed_summary.errors_found}
            </Badge>
          )}

          {agentResponse.detailed_summary.warnings_found > 0 && (
            <Badge className="bg-amber-900/30 text-amber-400">
              <AlertTriangle className="h-3 w-3 mr-1" /> {agentResponse.detailed_summary.warnings_found}
            </Badge>
          )}
        </div>
      </div>

      {/* Short summary - keep as is, it's already compact */}
      {agentResponse.short_summary && <div className="text-sm">{agentResponse.short_summary}</div>}

      {/* Tabs - more compact with smaller padding */}
      <Tabs defaultValue="events" className="w-full">
        <TabsList
          className="grid w-full"
          style={{
            gridTemplateColumns: `repeat(${
              [
                agentResponse.key_events?.length > 0 ? 1 : 0,
                sortedFlows.length > 0 ? 1 : 0,
                topSources.length > 0 ? 1 : 0,
                topDestinations.length > 0 ? 1 : 0,
              ].filter(Boolean).length
            }, minmax(0, 1fr))`,
          }}
        >
          {agentResponse.key_events?.length > 0 && <TabsTrigger value="events">Events</TabsTrigger>}

          {sortedFlows.length > 0 && <TabsTrigger value="flows">Flows</TabsTrigger>}

          {topSources.length > 0 && <TabsTrigger value="sources">Sources</TabsTrigger>}

          {topDestinations.length > 0 && <TabsTrigger value="destinations">Destinations</TabsTrigger>}
        </TabsList>

        {/* Key Events Tab */}
        {agentResponse.key_events?.length > 0 && (
          <TabsContent value="events" className="pt-2">
            <div className="max-h-[200px] overflow-y-auto pr-1">
              <div className="space-y-0.5">
                {agentResponse.key_events.map((event, index) => (
                  <div
                    key={index}
                    className={`flex items-start gap-2 py-1 px-2 text-xs border-l-2 hover:bg-slate-800/50 rounded-sm ${getSeverityClass(event.severity)}`}
                  >
                    {getSeverityIcon(event.severity)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <div className="font-medium truncate">{event.event_type}</div>
                        <div className="text-slate-400 shrink-0 ml-1">{event.timestamp}</div>
                      </div>
                      <div className="text-slate-300 mt-0.5">{event.description}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </TabsContent>
        )}

        {/* Flows Tab - Collapsible for details */}
        <TabsContent value="flows" className="pt-2">
          <div className="space-y-1 max-h-[200px] overflow-y-auto pr-1">
            {sortedFlows.map((flow, index) => (
              <Collapsible
                key={index}
                open={expandedFlowIndex === index}
                onOpenChange={() => setExpandedFlowIndex(expandedFlowIndex === index ? null : index)}
              >
                <Card className="overflow-hidden">
                  <CardContent className="p-2">
                    <CollapsibleTrigger className="flex items-center justify-between w-full">
                      <div className="flex items-center gap-2">
                        <Network className="h-4 w-4 text-blue-500" />
                        <div className="font-medium text-xs">
                          {flow.source} <ArrowRight className="h-3 w-3 inline mx-1" /> {flow.destination}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs py-0 px-1.5">
                          {flow.packet_count}
                        </Badge>
                        {expandedFlowIndex === index ? (
                          <ChevronDown className="h-3 w-3" />
                        ) : (
                          <ChevronRight className="h-3 w-3" />
                        )}
                      </div>
                    </CollapsibleTrigger>

                    <CollapsibleContent className="pt-1.5">
                      {flow.path.length > 0 && (
                        <div className="mt-1">
                          <div className="text-xs text-slate-400 mb-0.5">Path:</div>
                          <div className="flex items-center flex-wrap gap-1">
                            {flow.path.map((node, idx) => (
                              <div key={idx} className="flex items-center">
                                {idx > 0 && <ArrowRight className="h-3 w-3 text-slate-500 mx-0.5" />}
                                <Badge variant="secondary" className="text-xs py-0 px-1.5">
                                  {node}
                                </Badge>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {flow.relevant_log_pks.length > 0 && (
                        <div className="mt-1.5">
                          <div className="text-xs text-slate-400 mb-0.5">Log IDs:</div>
                          <div className="flex flex-wrap gap-1">
                            {flow.relevant_log_pks.slice(0, 3).map((id, idx) => (
                              <Badge key={idx} variant="outline" className="text-xs py-0 px-1.5 font-mono">
                                {id}
                              </Badge>
                            ))}
                            {flow.relevant_log_pks.length > 3 && (
                              <Badge variant="outline" className="text-xs py-0 px-1.5">
                                +{flow.relevant_log_pks.length - 3}
                              </Badge>
                            )}
                          </div>
                        </div>
                      )}
                    </CollapsibleContent>
                  </CardContent>
                </Card>
              </Collapsible>
            ))}
          </div>
        </TabsContent>

        {/* Sources Tab - More compact progress bars */}
        <TabsContent value="sources" className="pt-2">
          <div className="space-y-2 max-h-[200px] overflow-y-auto pr-1">
            {topSources.map(([source, count], index) => (
              <div key={index} className="space-y-0.5">
                <div className="flex items-center justify-between text-xs">
                  <div className="font-medium truncate mr-2">{source}</div>
                  <div className="text-slate-400 shrink-0">
                    {count} ({calculatePercentage(count)}%)
                  </div>
                </div>
                <Progress value={calculatePercentage(count)} className="h-1.5" />
              </div>
            ))}

            {Object.keys(agentResponse.detailed_summary.packets_by_source).length > 5 && (
              <div className="text-xs text-slate-400 text-center pt-1">
                +{Object.keys(agentResponse.detailed_summary.packets_by_source).length - 5} more
              </div>
            )}
          </div>
        </TabsContent>

        {/* Destinations Tab - More compact progress bars */}
        <TabsContent value="destinations" className="pt-2">
          <div className="space-y-2 max-h-[200px] overflow-y-auto pr-1">
            {topDestinations.map(([destination, count], index) => (
              <div key={index} className="space-y-0.5">
                <div className="flex items-center justify-between text-xs">
                  <div className="font-medium truncate mr-2">{destination}</div>
                  <div className="text-slate-400 shrink-0">
                    {count} ({calculatePercentage(count)}%)
                  </div>
                </div>
                <Progress value={calculatePercentage(count)} className="h-1.5" />
              </div>
            ))}

            {Object.keys(agentResponse.detailed_summary.packets_by_destination).length > 5 && (
              <div className="text-xs text-slate-400 text-center pt-1">
                +{Object.keys(agentResponse.detailed_summary.packets_by_destination).length - 5} more
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>

      {/* Issues Section - Collapsible for details */}
      {agentResponse.detailed_summary.detected_issues.length > 0 && (
        <div className="space-y-1">
          <div className="flex items-center gap-1 text-xs font-medium">
            <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
            <span>Issues ({agentResponse.detailed_summary.detected_issues.length})</span>
          </div>

          <div className="space-y-1 max-h-[100px] overflow-y-auto pr-1">
            {agentResponse.detailed_summary.detected_issues.map((issue, index) => (
              <Collapsible
                key={index}
                open={expandedIssueIndex === index}
                onOpenChange={() => setExpandedIssueIndex(expandedIssueIndex === index ? null : index)}
              >
                <Card className="overflow-hidden">
                  <CardContent className="p-2">
                    <CollapsibleTrigger className="flex items-start gap-2 w-full">
                      <AlertTriangle className="h-3.5 w-3.5 text-amber-500 mt-0.5 shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="text-xs truncate pr-5">{issue.description || JSON.stringify(issue)}</div>
                      </div>
                      <div className="absolute right-2 top-2">
                        {expandedIssueIndex === index ? (
                          <ChevronDown className="h-3 w-3" />
                        ) : (
                          <ChevronRight className="h-3 w-3" />
                        )}
                      </div>
                    </CollapsibleTrigger>

                    <CollapsibleContent className="pt-1.5">
                      {issue.affected_components && (
                        <div className="flex flex-wrap gap-1 mt-1 pl-5">
                          {issue.affected_components.map((component: string, idx: number) => (
                            <Badge key={idx} variant="outline" className="text-xs py-0 px-1.5">
                              {component}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </CollapsibleContent>
                  </CardContent>
                </Card>
              </Collapsible>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
