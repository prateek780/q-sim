import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuPortal,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { ChevronDown, ZoomIn, ZoomOut, RotateCcw, Beaker, Check, Bot } from "lucide-react"
import { downloadJson, exportToJSON } from "@/services/exportService"
import api from "@/services/api"
import { useState } from "react"
import { LabPanel } from "../labs/lab-panel"
import { Badge } from "../ui/badge"
import { EXERCISES } from "../labs/exercise "
import { set } from "lodash"
import { ExportDataI } from "@/services/export.interface"
import simulationState from "@/helpers/utils/simulationState"

interface TopBarProps {
  onStartLab?: (labId: string) => void
  completedLabs?: string[]
  simulationStateUpdateCount: any
  updateLabProgress: (completed: number, total: number) => void
  onOpenAIPanel?: () => void
}

export function TopBar({
  onStartLab = () => { },
  completedLabs = [],
  simulationStateUpdateCount,
  updateLabProgress,
  onOpenAIPanel = () => { },
}: TopBarProps
) {
  const [isLabPanelOpen, setIsLabPanelOpen] = useState(false)
  const [savedTopologies, setSavedTopologies] = useState([])


  const fetchSavedTopologies = async () => {
    const response = await api.listSavedTopologies();
    if (response) {
      setSavedTopologies(response);
    }
  }

  const exportJSONFile = () => {
    const jsonData = exportToJSON();

    if (!jsonData) return;

    downloadJson(jsonData, "network")
  }

  const saveCurrentNetwork = async () => {
    const jsonData = exportToJSON();

    if (!jsonData) return;

    const activeTopologyID = simulationState.getWorldId();
    if (activeTopologyID)
      jsonData.pk = activeTopologyID;
    else
      jsonData.name = prompt("Enter a name for the topology") || "Untitled Topology";

    const response = await api.saveTopology(jsonData);

    if (response?.pk) {
      simulationState.setWorldId(response.pk);
    } else {
      console.error("Failed to save topology");
    }
  }

  return (
    <>

      <div className="h-12 border-b border-slate-700 bg-slate-800 flex items-center justify-between px-4">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-bold bg-gradient-to-r from-purple-400 to-blue-500 bg-clip-text text-transparent">
            Quantum Network Simulator
          </h1>

          <div className="flex items-center">
            <DropdownMenu onOpenChange={fetchSavedTopologies}>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="h-8 gap-1">
                  File <ChevronDown className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => (window.location.href = "/")}>New Project</DropdownMenuItem>
                <DropdownMenuItem onClick={saveCurrentNetwork}>Save</DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={exportJSONFile}>Export...</DropdownMenuItem>
                <DropdownMenuItem>Import...</DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuSub>
                  <DropdownMenuSubTrigger>Load Saved Topology</DropdownMenuSubTrigger>
                  <DropdownMenuPortal>
                    <DropdownMenuSubContent>
                      {
                        savedTopologies.length === 0 ?
                          <DropdownMenuItem disabled>
                            No saved topologies found.
                          </DropdownMenuItem>
                          :
                          savedTopologies.map((topology: ExportDataI) => (
                            <DropdownMenuItem
                              key={topology.pk}
                              onClick={() => {
                                window.location.href = `/?topologyID=${topology.pk}`;
                              }}
                            >
                              {topology.name}
                            </DropdownMenuItem>
                          ))
                      }
                    </DropdownMenuSubContent>
                  </DropdownMenuPortal>
                </DropdownMenuSub>
              </DropdownMenuContent>
            </DropdownMenu>

            {/* <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-8 gap-1">
                Edit <ChevronDown className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem>Undo</DropdownMenuItem>
              <DropdownMenuItem>Redo</DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem>Cut</DropdownMenuItem>
              <DropdownMenuItem>Copy</DropdownMenuItem>
              <DropdownMenuItem>Paste</DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem>Select All</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu> */}

            {/* <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-8 gap-1">
                View <ChevronDown className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem>Zoom In</DropdownMenuItem>
              <DropdownMenuItem>Zoom Out</DropdownMenuItem>
              <DropdownMenuItem>Fit to Screen</DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem>Show Grid</DropdownMenuItem>
              <DropdownMenuItem>Show Labels</DropdownMenuItem>
              <DropdownMenuItem>Show Quantum States</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu> */}

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="h-8 gap-1">
                  Simulation <ChevronDown className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem>Run</DropdownMenuItem>
                {/* <DropdownMenuItem>Pause</DropdownMenuItem> */}
                <DropdownMenuItem>Stop</DropdownMenuItem>
                <DropdownMenuItem>Reset</DropdownMenuItem>
                <DropdownMenuSeparator />
                {/* <DropdownMenuItem>Configure Parameters...</DropdownMenuItem>
              <DropdownMenuItem>Export Results...</DropdownMenuItem> */}
              </DropdownMenuContent>
            </DropdownMenu>

            {/* New Lab Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="h-8 gap-1">
                  Lab <ChevronDown className="h-4 w-4" />
                  <Badge className="ml-1 h-5 bg-blue-600 hover:bg-blue-700">
                    {completedLabs.length}/{EXERCISES.length}
                  </Badge>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => setIsLabPanelOpen(true)}>
                  <Beaker className="h-4 w-4 mr-2" />
                  Browse Labs
                </DropdownMenuItem>
                {/* <DropdownMenuItem>
                  <Award className="h-4 w-4 mr-2" />
                  My Progress
                </DropdownMenuItem> */}
                <DropdownMenuSeparator />
                {
                  EXERCISES.map((exercise) => (
                    <DropdownMenuItem key={exercise.id}>
                      {exercise.title}
                      {completedLabs.includes(exercise.id) && <Check className="h-4 w-4 ml-2 text-green-500" />}
                    </DropdownMenuItem>
                  ))
                }
              </DropdownMenuContent>
            </DropdownMenu>

          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center border rounded-md overflow-hidden">
            <Button variant="ghost" size="icon" className="h-8 w-8 rounded-none border-r">
              <ZoomOut className="h-4 w-4" />
            </Button>
            <Input type="text" defaultValue={"100%"} className="h-8 w-16 border-0 rounded-none text-center" />
            <Button variant="ghost" size="icon" className="h-8 w-8 rounded-none border-l">
              <ZoomIn className="h-4 w-4" />
            </Button>
          </div>

          <Button size="sm" className="h-8 gap-1" onClick={onOpenAIPanel}>
            <Bot className="h-4 w-4" />
            AI Agents
          </Button>

          <Button variant="ghost" size="icon" className="h-8 w-8">
            <RotateCcw className="h-4 w-4" />
          </Button>

          {/* <Button variant="ghost" size="icon" className="h-8 w-8">
          <Grid className="h-4 w-4" />
        </Button>

        <Button variant="ghost" size="icon" className="h-8 w-8">
          <Layers className="h-4 w-4" />
        </Button>

        <Button variant="ghost" size="icon" className="h-8 w-8">
          <Download className="h-4 w-4" />
        </Button> */}
        </div>
      </div>
      {/* Lab Panel */}
      <LabPanel
        isOpen={isLabPanelOpen}
        onClose={() => setIsLabPanelOpen(false)}
        simulationState={simulationStateUpdateCount}
        onStartLab={onStartLab}
        updateLabProgress={updateLabProgress}
      />
    </>
  )
}

