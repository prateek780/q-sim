import { exportToJSON } from "@/services/exportService";
import ReactJsonView from '@microlink/react-json-view';
import { NetworkManager } from "../node/network/networkManager";

export function JSONFormatViewer() {
    if(!NetworkManager.getInstance()?.getAllNetworks()) {
        return (
            <div className="flex flex-col items-center justify-center h-full p-8 text-center">
            <p className="text-slate-400">Build Network To See This</p>
            </div>
        )
    }
    
    const jsonFormat = exportToJSON() as Object;
    
    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">JSON View</h3>
            </div>

            <ReactJsonView src={jsonFormat} theme={"tomorrow"}/>
        </div>
    )
}