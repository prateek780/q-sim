class SimulationState {
    private simulationRunning = false;
    private simulationID: string | null = null;
    private worldId: string | null = null;

    setSimulationID(simulationID: string | null) {
        this.simulationID = simulationID;
    }

    getSimulationID() {
        return this.simulationID;
    }

    setSimulationRunning(isRunning: boolean) {
        this.simulationRunning = isRunning;
    }

    getSimulationRunning() {
        return this.simulationRunning;
    }

    setWorldId(worldId: string | null) {
        this.worldId = worldId;
    }

    getWorldId() {
        return this.worldId;
    }
}

export default new SimulationState();