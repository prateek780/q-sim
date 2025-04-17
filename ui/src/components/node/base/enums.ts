export enum SimulationNodeType {
    CLASSICAL_HOST,
    CLASSICAL_ROUTER,
    CLASSICAL_NETWORK,
    INTERNET_EXCHANGE,
    QUANTUM_ADAPTER,
    QUANTUM_HOST,
    QUANTUM_REPEATER,
    CLASSIC_TO_QUANTUM_CONVERTER,
    QUANTUM_TO_CLASSIC_CONVERTER,
    ZONE,
}

export function getSimulationNodeTypeString(nodeType: SimulationNodeType): string {
    switch (nodeType) {
        case SimulationNodeType.CLASSICAL_HOST:
            return "Classical Host";
        case SimulationNodeType.CLASSICAL_ROUTER:
            return "Classical Router";
        case SimulationNodeType.CLASSICAL_NETWORK:
            return "Classical Network";
        case SimulationNodeType.INTERNET_EXCHANGE:
            return "Internet Exchange";
        case SimulationNodeType.QUANTUM_ADAPTER:
            return "Quantum Adapter";
        case SimulationNodeType.QUANTUM_HOST:
            return "Quantum Host";
        case SimulationNodeType.QUANTUM_REPEATER:
            return "Quantum Repeater";
        case SimulationNodeType.CLASSIC_TO_QUANTUM_CONVERTER:
            return "Classic to Quantum Converter";
        case SimulationNodeType.QUANTUM_TO_CLASSIC_CONVERTER:
            return "Quantum to Classic Converter";
        case SimulationNodeType.ZONE:
            return "Zone";
        default:
            return "Unknown Node Type";
    }
}

export function getNodeFamily(node: SimulationNodeType): NodeFamily {
    if (node === SimulationNodeType.CLASSICAL_HOST || node === SimulationNodeType.CLASSICAL_ROUTER || node === SimulationNodeType.CLASSICAL_NETWORK || node === SimulationNodeType.INTERNET_EXCHANGE) {
        return NodeFamily.CLASSICAL;
    } else if (node === SimulationNodeType.QUANTUM_HOST || node === SimulationNodeType.QUANTUM_REPEATER) {
        return NodeFamily.QUANTUM;
    }
    return NodeFamily.HYBRID;
}

export enum NodeFamily {
    CLASSICAL,
    QUANTUM,
    HYBRID
}