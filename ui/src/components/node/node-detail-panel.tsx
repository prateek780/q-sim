"use client"

import { useEffect, useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { Separator } from "@/components/ui/separator"
import { Cpu, Activity, Code, EthernetPort } from "lucide-react"
import { MessagingPanel } from "../metrics/messaging-panel"
import { ClassicalHost } from "./classical/classicalHost"
import { SimulatorNode } from "./base/baseNode"
import { NetworkManager } from "./network/networkManager"
import { toast } from "sonner"
import { SimulatorConnection } from "./connections/line"
import { ConnectionManager } from "./connections/connectionManager"

interface NodeDetailPanelProps {
  selectedNode: SimulatorNode | null
  onSendMessage?: (source: string, target: string, message: string, protocol: string) => void
  isSimulationRunning?: boolean
}

export function NodeDetailPanel({
  selectedNode,
  onSendMessage = () => { },
  isSimulationRunning = false,
}: NodeDetailPanelProps) {
  const [activeTab, setActiveTab] = useState("properties")
  const [isHost, setIsHost] = useState(false)
  const [connections, setConnections] = useState<SimulatorConnection[]>([]);
  const [selectedConnection, setSelectedConnection] = useState<SimulatorConnection | null>(null);

  useEffect(() => {
    ConnectionManager.getInstance()?.onConnectionCallback(updateConnections);
  }, [])

  useEffect(() => {
    setIsHost(selectedNode instanceof ClassicalHost);
    updateConnections();
  }, [selectedNode])

  const updateConnections = (...args: any[]) => {
    const connectionManager = ConnectionManager.getInstance();
    if (connectionManager) {
      setConnections(connectionManager.getAllConnections().filter((c) => c.metaData.from === selectedNode || c.metaData.to === selectedNode));
    }
  };

  if (!selectedNode) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center">
        <p className="text-slate-400">Select a node to view its details</p>
      </div>
    )
  }

  const onNameChange = (event: any) => {
    const newName = event.target.value;
    const isDuplicate = NetworkManager.getInstance().canvas.getObjects().filter(x => x instanceof SimulatorNode).some(x => x.name === newName);
    if (isDuplicate) {
      // toast('Name Already Used');
      alert('Name Already Used');
      return;
    }
    selectedNode.name = newName;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-md bg-green-500">
          <Cpu className="h-5 w-5" />
        </div>
        <div>
          <h3 className="text-lg font-medium">{selectedNode.name}</h3>
          <p className="text-sm text-slate-400">Quantum Host</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid grid-cols-4">
          <TabsTrigger value="properties">Properties</TabsTrigger>
          {/* <TabsTrigger value="behavior">Behavior</TabsTrigger> */}
          {/* <TabsTrigger value="code">Code</TabsTrigger> */}
          {isHost && <TabsTrigger value="messaging">Messaging</TabsTrigger>}
        </TabsList>

        <TabsContent value="properties" className="space-y-4 pt-4">
          <div className="grid gap-4">
            <div className="grid gap-2">
              <Label htmlFor="node-name">Name</Label>
              <Input id="node-name" defaultValue={selectedNode.name} onChange={onNameChange} />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="node-type">Type</Label>
              <Select defaultValue="quantum-host" disabled>
                <SelectTrigger id="node-type">
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="quantum-host">Quantum Host</SelectItem>
                  <SelectItem value="quantum-adapter">Quantum Adapter</SelectItem>
                  <SelectItem value="classical-host">Classical Host</SelectItem>
                  <SelectItem value="classical-router">Classical Router</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Separator />

            <div className="flex items-center gap-3">
              <EthernetPort className="h-5 w-5 text-slate-400" />
              <h3 className="text-lg font-medium">Connection Settings</h3>
            </div>


            <div className="grid gap-2">
              <Label htmlFor="node-type">Connection From</Label>
              <Select
                disabled={connections.length === 0}
                defaultValue={connections.length > 0 ? (connections[0].metaData.from === selectedNode ? connections[0].metaData.to?.name : connections[0].metaData.from?.name) : 'na'}
                onValueChange={(value) => {
                  const connection = connections.find(conn => conn.metaData.from === selectedNode && conn.metaData.to?.name === value) || connections.find(conn => conn.metaData.to === selectedNode && conn.metaData.from?.name === value);
                  setSelectedConnection(connection || null);
                }}
              >
                <SelectTrigger id="node-type">
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="na">N/A</SelectItem>
                  {
                    connections.map(conn => {
                      const otherNode = conn.metaData.from === selectedNode ? conn.metaData.to : conn.metaData.from;
                      if (!otherNode) {
                        return null;
                      }
                      return <SelectItem key={otherNode?.name} value={otherNode?.name}>{otherNode.name}</SelectItem>
                    })
                  }
                </SelectContent>
              </Select>
            </div>

            {/* {selectedConnection ? <div className="grid gap-2">
              <Label htmlFor="losskm">Loss Per Kilometer</Label>
              <div className="flex items-center gap-4">
                <Slider
                  id="losskm"
                  defaultValue={[0.1]}
                  max={10}
                  min={0.1}
                  step={0.1}
                  className="flex-1"
                  onValueChange={(val) => selectedConnection.metaData.lossPerKm = val[0]}
                />
                <span className="w-8 text-center">{selectedConnection.metaData.lossPerKm}/km</span>
              </div>
            </div> : 'Select Connection'} */}

            {
              selectedConnection ?
                <div className="grid gap-2">
                  <Label htmlFor="node-name">Loss per kilometer</Label>
                  <Input id="node-name" defaultValue={selectedConnection.metaData.lossPerKm} onChange={e => selectedConnection.metaData.lossPerKm = +e.target.value} type="number" />
                </div> : 'Select Connection'
            }

            {/* <div className="grid gap-2">
              <Label htmlFor="error-rate">Error Rate (%)</Label>
              <div className="flex items-center gap-4">
                <Slider
                  id="error-rate"
                  defaultValue={[1]}
                  max={5}
                  min={0}
                  step={0.1}
                  className="flex-1"
                />
                <span className="w-12 text-center">1%</span>
              </div>
            </div> */}

            {/* <div className="grid gap-2">
              <Label htmlFor="coherence-time">Coherence Time (μs)</Label>
              <div className="flex items-center gap-4">
                <Slider
                  id="coherence-time"
                  defaultValue={[1]}
                  max={500}
                  min={10}
                  step={10}
                  className="flex-1"
                />
                <span className="w-12 text-center">{1}</span>
              </div>
            </div> */}

            {/* <div className="grid gap-2">
              <Label htmlFor="protocol">Quantum Protocol</Label>
              <Select defaultValue={'BB84'}>
                <SelectTrigger id="protocol">
                  <SelectValue placeholder="Select protocol" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="BB84">BB84</SelectItem>
                  <SelectItem value="E91">E91</SelectItem>
                  <SelectItem value="B92">B92</SelectItem>
                  <SelectItem value="CUSTOM">Custom</SelectItem>
                </SelectContent>
              </Select>
            </div> */}
          </div>
        </TabsContent>

        {/* <TabsContent value="behavior" className="space-y-4 pt-4">
          <div className="grid gap-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-slate-400" />
                <Label htmlFor="decoherence">Simulate Decoherence</Label>
              </div>
              <Switch id="decoherence" defaultChecked />
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-slate-400" />
                <Label htmlFor="gate-errors">Gate Errors</Label>
              </div>
              <Switch id="gate-errors" defaultChecked />
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-slate-400" />
                <Label htmlFor="measurement-errors">Measurement Errors</Label>
              </div>
              <Switch id="measurement-errors" defaultChecked />
            </div>

            <Separator />

            <div className="grid gap-2">
              <Label htmlFor="behavior-model">Behavior Model</Label>
              <Select defaultValue="realistic">
                <SelectTrigger id="behavior-model">
                  <SelectValue placeholder="Select model" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ideal">Ideal (No Errors)</SelectItem>
                  <SelectItem value="simplified">Simplified</SelectItem>
                  <SelectItem value="realistic">Realistic</SelectItem>
                  <SelectItem value="custom">Custom</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="environment">Environment</Label>
              <Select defaultValue="room-temp">
                <SelectTrigger id="environment">
                  <SelectValue placeholder="Select environment" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="room-temp">Room Temperature</SelectItem>
                  <SelectItem value="cryogenic">Cryogenic</SelectItem>
                  <SelectItem value="vacuum">Vacuum</SelectItem>
                  <SelectItem value="custom">Custom</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </TabsContent> */}

        {/* <TabsContent value="code" className="pt-4">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Label htmlFor="code-editor">Custom Behavior Code</Label>
              <Button variant="outline" size="sm">
                <Code className="h-4 w-4 mr-2" />
                Validate
              </Button>
            </div>
            <div className="relative">
              <div className="absolute inset-0 bg-slate-900 rounded-md p-4 font-mono text-sm overflow-auto">
                <pre className="text-green-400">
                  {`// Quantum Host behavior
                    function initializeNode() {
                    // Initialize qubits in |0⟩ state
                    for (let i = 0; i < this.qubits; i++) {
                      this.initQubit(i);
                    }

                    // Apply Hadamard to create superposition
                    this.applyGate("H", 0);

                    // Setup entanglement with target
                    if (this.connections.length > 0) {
                      this.entangle(0, this.connections[0], 0);
                    }
                  }`}
                </pre>
              </div>
              <div className="h-64"></div>
            </div>
          </div>
        </TabsContent> */}

        {isHost && (
          <TabsContent value="messaging" className="pt-4">
            <MessagingPanel
              selectedNode={selectedNode}
              onSendMessage={onSendMessage}
              isSimulationRunning={isSimulationRunning}
            />
          </TabsContent>
        )}
      </Tabs>
    </div>
  )
}

