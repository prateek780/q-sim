import { QuantumAdapter } from "../components/node/base/quantum/quantumAdapter";
import { NetworkManager } from "../components/node/network/networkManager";
import { getLogger } from "../helpers/simLogger";
import { ExportDataI, ZoneI } from "./export.interface";

export function exportToJSON(): ExportDataI | undefined {
    const logger = getLogger("ExportService");
    const networks = NetworkManager.getInstance()?.getAllNetworks();

    if (!networks) {
        logger.error("No networks found.");
        return;
    }

    const exportData: ExportDataI = {
        // networks: networks.map(network => network.toExportJson())
        "name": "My World",
        "size": [100, 100],
        "zones": networks.map((network, i) => {
            const adapters: Array<QuantumAdapter> = [];
            NetworkManager.getInstance()?.canvas.getObjects().forEach((obj) => {
                // If a QuantumAdapter is found and it is connected to this channel, add it to the export data in this zone.
                if (obj instanceof QuantumAdapter && obj.quantumHost && network.connectedNodes.has(obj.quantumHost)) {
                    adapters.push(obj);
                }
            });
            const zone: ZoneI = {
                "name": "Zone " + i,
                "type": "SECURE",
                "size": [network.getX() + network.width, network.getY() + network.height],
                "position": [network.getX(), network.getY()],
                'networks': [network.toExportJson()],
                "adapters": adapters.map(adapter => adapter.toExportJson()).filter(x => x != undefined)
            }
            return zone
        })
    }
    let maxWidth = 0;
    let maxHeight = 0;


    exportData.zones.forEach((zone) => {
        if (zone.size[0] + zone.position[0] > maxWidth) {
            maxWidth = zone.size[0] + zone.position[0];
        }
        if (zone.size[1] + zone.position[1] > maxHeight) {
            maxHeight = zone.size[1] + zone.position[1];
        }
    });

    exportData.size = [maxWidth + 100, maxHeight + 100];

    // downloadJson(exportData, "network");
    return exportData;
}

export function downloadJson(storageObj: any, exportName: string) {
    var dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(storageObj));
    var downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", exportName + ".json");
    document.body.appendChild(downloadAnchorNode); // required for firefox
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
}