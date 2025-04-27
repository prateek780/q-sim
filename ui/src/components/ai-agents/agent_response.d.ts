export interface AgentResponse {
}

export interface LogSummaryResponse extends AgentResponse {
    simulation_id: string
    summary_period: SummaryPeriod
    short_summary: string
    detailed_summary: DetailedSummary
}

export interface SummaryPeriod {
    start: string
    end: string
}

export interface DetailedSummary {
    total_packets_transmitted: number
    packets_by_source: {[key: string]: number}
    packets_by_destination: {[key: string]: number}
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
