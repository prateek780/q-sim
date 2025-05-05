import { ExportDataI } from "./export.interface"

export interface StartSimulationResponse {
    pk: string
    name: string
    world_id: string
    status: string
    start_time: string
    last_updated: string
    end_time: any
    configuration: ExportDataI
    metrics: any
}