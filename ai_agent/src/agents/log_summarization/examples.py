from ai_agent.src.agents.log_summarization.structures import (
    LogSummaryOutput,
    SummarizeInput,
)
from ai_agent.src.agents.topology_agent.structure import (
    SynthesisTopologyOutput,
    SynthesisTopologyRequest,
)


OUTPUT_EXAMPLE = {
    "simulation_id": "01JSMD4079X4VYT3JPN60ZWHHY",
    "summary_period": {
        "start": "2025-04-24T17:22:04.549561",
        "end": "2025-04-24T17:22:32.792760",
    },
    "short_summary": "The simulation involves classical data transfer from ClassicalHost-5 to ClassicalHost-1, and QKD key exchange between QuantumHost-8 and QuantumHost-3. The classical data traverses through ClassicalRouter-4 and ClassicalRouter-2, while the QKD key exchange involves QuantumAdapters connected to these routers.",
    "key_events": [
        {
            "timestamp": "2025-04-24T17:22:04.549561",
            "event_type": "info",
            "description": "The simulation starts with the classical data transfer from ClassicalHost-5 to ClassicalRouter-4.",
            "severity": "info"
        },
        {
            "timestamp": "2025-04-24T17:22:32.792760",
            "event_type": "info",
            "description": "The simulation proceeds with the QKD key exchange between QuantumHost-8 and QuantumHost-3.",
            "severity": "info"
        },
        {
            "timestamp": "2025-04-24T17:22:32.792760",
            "event_type": "info",
            "description": "The simulation concludes with the QKD key exchange between QuantumHost-8 and QuantumHost-3.",
            "severity": "info"
        }
    ],
    "detailed_summary": {
        "total_packets_transmitted": 7,
        "packets_by_source": {
            "ClassicalHost-5-ClassicalRouter-4": 1,
            "ClassicalRouter-2-ClassicalHost-1": 1,
            "QC_Router_Connection": 2,
            "Router - 'ClassicalRouter-4' QuantumAdapter - 'QuantumAdapter-7' Connection": 1,
            "ClassicalHost-5": 0,
            "Router - 'ClassicalRouter-2' QuantumAdapter - 'QuantumAdapter-6' Connection": 1,
        },
        "packets_by_destination": {
            "ClassicalHost-1": 2,
            "QC_Router_QuantumAdapter-6": 3,
            "QC_Router_QuantumAdapter-7": 2,
        },
        "communication_flows": [
            {
                "source": "ClassicalHost-5",
                "destination": "ClassicalHost-1",
                "packet_count": 1,
                "path": [
                    "ClassicalHost-5",
                    "ClassicalRouter-4",
                    "QC_Router_QuantumAdapter-7",
                    "QC_Router_QuantumAdapter-6",
                    "ClassicalRouter-2",
                    "ClassicalHost-1",
                ],
                "relevant_log_pks": [
                    "01JSMD497639GXDE3M2HQKS6YN",
                    "01JSMD4CACFZVAX7DFMPPCREK9",
                    "01JSMD4EQ405SFGHBJHF94C7MF",
                    "01JSMD54GJEM4SRZK3688JD6Z6",
                ],
            },
            {
                "source": "ClassicalHost-5",
                "destination": "QC_Router_QuantumAdapter-7",
                "packet_count": 1,
                "path": [
                    "ClassicalHost-5",
                    "ClassicalRouter-4",
                    "QC_Router_QuantumAdapter-7",
                ],
                "relevant_log_pks": [
                    "01JSMD497639GXDE3M2HQKS6YN",
                    "01JSMD4CACFZVAX7DFMPPCREK9",
                    "01JSMD4EQ405SFGHBJHF94C7MF",
                ],
            },
            {
                "source": "QC_Router_QuantumAdapter-7",
                "destination": "QC_Router_QuantumAdapter-6",
                "packet_count": 2,
                "path": ["QC_Router_QuantumAdapter-7", "QC_Router_QuantumAdapter-6"],
                "relevant_log_pks": [
                    "01JSMD4TKJM86QGM4243NBBMXE",
                    "01JSMD4TA3Z3SKEPKGMZWHCNXK",
                ],
            },
        ],
        "errors_found": 0,
        "warnings_found": 0,
        "detected_issues": [],
    },
}

INPUT_EXAMPLE = {
    "simulation_id": "01JSM8YQ4QZQZQZQZQZQZQZQZQ",
    "conversation_id": "1231232",
}


LOG_SUMMARY_EXAMPLES = [
    {
        "input": SummarizeInput(**INPUT_EXAMPLE).model_dump_json(),
        "output": LogSummaryOutput(**OUTPUT_EXAMPLE).model_dump_json(),
    }
]
