import { LogI } from "./simulation-logs";

export function convertEventToLog(event: any): LogI | undefined {
    const time = new Date(event.timestamp * 1000).toLocaleTimeString();
    const source = event.node;
    let message = "";

    switch (event.event_type) {
        case "data_sent":
            message = `Sending message "${transformData(event.data.data)}" to ${getNodeName(event.data.destination)}`;
            break;
        case "data_received":
            message = `Data Received: ${transformData(event.data.data)}`;
            break;
        case "packet_transmitted":
            return;
            // It might be good to ignore this packet and display animation instead. Kept for reference.
            try {
                // Parse the nested packet JSON string
                const packetData = JSON.parse(event.data.packet.replace("Packet -> ", ""));
                const from = packetData.from.replace(/Host - |'|"/g, "");
                const to = packetData.to.replace(/Host - |'|"/g, "");
                const data = packetData.data;

                message = `Transmitting data "${data}" from ${from} to ${to}`;
            } catch (e) {
                // Fallback if parsing fails
                message = `Transmitting packet`;
            }
            break;
        case "packet_received":
            message = `Received packet from ${extractSender(event.data.packet)}`;

            const extractedMessage = transformData(event.data.packet.data);
            if(extractedMessage) {
                message += ` with data ${extractedMessage}`;
            }
            break;
        case "qkd_initiated":
            message = `Initiated quantum key distribution with ${getNodeName(event.data.with_adapter)}`;
            break;
        case "classical_data_received":
            if (event.data.message?.type === 'shared_bases_indices') {
                message = `Received shared quantum bases from ${getNodeName(event.data.message.sender)}`;
            } else if (event.data.message?.type === 'reconcile_bases') {
                message = `Reconciling quantum bases`;
            } else if (event.data.message?.type === 'estimate_error_rate') {
                message = `Estimating quantum channel error rate`;
            } else if (event.data.message?.type === 'complete') {
                message = `Quantum key exchange completed successfully`;
            } else {
                message = `Received data: ${JSON.stringify(event.data.message)}`;
            }
            break;
        default:
            console.warn(`Un-handled event ${event.event_type} Received`, event);
            message = `${event.event_type}: ${JSON.stringify(event.data)}`;
    }

    return {
        level: "info",
        time: time,
        source: source,
        message: message
    };
}

// Helper functions
function getNodeName(node: any): string {
    if (!node) return "unknown";
    if (typeof node === 'string') return node;
    return node.name || "unknown";
}

function transformData(data: any): string {
    if (data instanceof ArrayBuffer || data?.toString().startsWith('bytearray')) {
        return "[Encrypted Data]";
    }
    return data?.toString() || "";
}

function extractSender(packetStr: any): string {
    if (!packetStr) return "unknown";

    // Extract the "from" field from the packet string
    // const fromMatch = packetStr.match(/"from":\s*"([^"]+)"/);
    const fromMatch = packetStr['hops'][packetStr['hops'].length - 1]  || packetStr['from'];
    // return fromMatch ? fromMatch[1] : "unknown";
    return fromMatch;
}