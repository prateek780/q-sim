import { ExportDataI } from "@/services/export.interface"

export interface AgentResponse {
}

//  ================== LOG SUMMARY ===================
export interface LogSummaryResponse extends AgentResponse {
    simulation_id: string
    summary_period: SummaryPeriod
    short_summary: string
    key_events: KeyLogEvent[]
    detailed_summary: DetailedSummary
}

export interface KeyLogEvent {
    timestamp: string
    event_type: string
    description: string
    severity: "info" | "warning" | "error" | "success"
}


export interface SummaryPeriod {
    start: string
    end: string
}

export interface DetailedSummary {
    total_packets_transmitted: number
    packets_by_source: { [key: string]: number }
    packets_by_destination: { [key: string]: number }
    communication_flows: CommunicationFlow[]
    errors_found: number
    warnings_found: number
    detected_issues: any[]
}

export interface CommunicationFlow {
    source: string
    destination: string
    packet_count: number
    path: string[]
    relevant_log_pks: string[]
}

// ================== LOG QNA RESPONSE ===================
export interface LogQnaResponse extends AgentResponse {
    status: string
    answer: string
    cited_log_entries: any
    error_message: any
  }
  

// ================== ORCHESTRATOR RESPONSE ===================
export interface OrchestratorResponse extends AgentResponse {
    agent_id: string
    task_id: string
    input_data: InputData
    reason: string
    suggestion: any
    agent_response: AgentResponse
}

// ================== TOPOLOGY OPTIMIZER RESPONSE ===================
export interface TopologyOptimizerResponse extends AgentResponse {
    original_topology: ExportDataI
    optimized_topology: ExportDataI
    overall_feedback: string
    cost: number
    optimization_steps: OptimizationStep[]
}


export interface OptimizationStep {
    change_path: string[]
    change: string
    reason: string
    citation: any[]
    comments: string
}

// =============== TOPOLOGY GENERATION RESPONSE =======================
export interface TopologyGenerationResponse {
    error: string
    success: boolean
    generated_topology: ExportDataI
    overall_feedback: string
    cost: number
    thought_process: string[]
}

// ================== TOPOLOGY QnA RESPONSE ===================
export interface TopologyQnAResponse {
    status: string
    answer: string
    relevant_topology_parts: RelevantTopologyPart[]
    error_message: any
    message_id: string
}

export interface RelevantTopologyPart {
    path: string
    snippet: string
}