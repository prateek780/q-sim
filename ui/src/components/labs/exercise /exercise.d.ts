export interface ExerciseI {
    id: string
    title: string
    description: string
    difficulty: string
    estimatedTime: string
    category: string
    steps: string[]
    requirements: ExerciseRequirements
    tips: string[]
}

export interface ExerciseRequirements {
    nodes: SimulationNodeType[]
    connections: SimulationNodeType[][]
    simulation: boolean
    entanglement?: boolean
    messages?: number
}
