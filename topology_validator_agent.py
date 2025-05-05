from typing import Dict, Any, List, Optional
import json
import re
from dataclasses import dataclass
from enum import Enum, auto

class NetworkType(Enum):
    CLASSICAL_NETWORK = "CLASSICAL_NETWORK"
    QUANTUM_NETWORK = "QUANTUM_NETWORK"
    HYBRID_NETWORK = "HYBRID_NETWORK"

class NodeType(Enum):
    CLIENT = "CLIENT"
    CLASSICAL_ROUTER = "CLASSICAL_ROUTER"
    QUANTUM_HOST = "QUANTUM_HOST"
    QUANTUM_ADAPTER = "QUANTUM_ADAPTER"

class ConnectionType(Enum):
    CLASSICAL_LINK = "CLASSICAL_LINK"
    QUANTUM_CHANNEL = "QUANTUM_CHANNEL"
    HYBRID_LINK = "HYBRID_LINK"

@dataclass
class ValidationResult:
    is_valid: bool
    confidence_score: float
    issues: List[str]
    recommendations: List[str]

class TopologyValidatorAgent:
    def __init__(self):
        self.required_fields = {
            "zone": ["name", "type", "size", "position", "networks"],
            "network": ["name", "type", "hosts", "connections"],
            "host": ["name", "type", "address", "location"],
            "connection": ["from_node", "to_node", "bandwidth", "latency", "length", "loss_per_km", "noise_model"]
        }
        
        self.network_type_patterns = {
            NetworkType.CLASSICAL_NETWORK: r"classical|traditional|standard",
            NetworkType.QUANTUM_NETWORK: r"quantum|qkd|entanglement",
            NetworkType.HYBRID_NETWORK: r"hybrid|mixed|both"
        }
        
        self.node_type_patterns = {
            NodeType.CLIENT: r"host|client|endpoint|computer",
            NodeType.CLASSICAL_ROUTER: r"router|switch|gateway",
            NodeType.QUANTUM_HOST: r"quantum\s*host|quantum\s*node|qkd\s*node",
            NodeType.QUANTUM_ADAPTER: r"adapter|converter|interface"
        }

        self.connection_type_patterns = {
            ConnectionType.CLASSICAL_LINK: r"classical\s+link|classical\s+connection|standard\s+connection",
            ConnectionType.QUANTUM_CHANNEL: r"quantum\s+channel|quantum\s+link|entanglement\s+channel",
            ConnectionType.HYBRID_LINK: r"hybrid\s+link|hybrid\s+connection|mixed\s+connection"
        }

    def validate_topology(self, query: str, topology_data: Dict[str, Any]) -> ValidationResult:
        """Validate the generated topology against the user query requirements"""
        try:
            # First validate the basic structure
            if not self._validate_structure(topology_data):
                return ValidationResult(
                    is_valid=False,
                    confidence_score=0.0,
                    issues=["Invalid topology structure"],
                    recommendations=["Check the topology JSON structure"]
                )

            requirements = self.parse_user_query(query)
            issues = []
            recommendations = []
            
            # Validate network types
            network_issues, network_recs = self._validate_network_types(topology_data, requirements)
            issues.extend(network_issues)
            recommendations.extend(network_recs)
            
            # Validate node counts
            node_issues, node_recs = self._validate_node_counts(topology_data, requirements)
            issues.extend(node_issues)
            recommendations.extend(node_recs)
            
            # Validate connections
            conn_issues, conn_recs = self._validate_connections(topology_data, requirements)
            issues.extend(conn_issues)
            recommendations.extend(conn_recs)
            
            # Validate security requirements
            sec_issues, sec_recs = self._validate_security(topology_data, requirements)
            issues.extend(sec_issues)
            recommendations.extend(sec_recs)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(issues)
            
            return ValidationResult(
                is_valid=len(issues) == 0,
                confidence_score=confidence_score,
                issues=issues,
                recommendations=recommendations
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                issues=[f"Error during validation: {str(e)}"],
                recommendations=["Check the topology data format and try again"]
            )

    def _validate_structure(self, topology: Dict[str, Any]) -> bool:
        """Validate the basic structure of the topology"""
        try:
            if not isinstance(topology, dict):
                return False
            
            if "zones" not in topology:
                return False
            
            for zone in topology["zones"]:
                if not all(field in zone for field in self.required_fields["zone"]):
                    return False
                
                for network in zone.get("networks", []):
                    if not all(field in network for field in self.required_fields["network"]):
                        return False
                    
                    for host in network.get("hosts", []):
                        if not all(field in host for field in self.required_fields["host"]):
                            return False
                    
                    for conn in network.get("connections", []):
                        if not all(field in conn for field in self.required_fields["connection"]):
                            return False
            
            return True
        except Exception:
            return False

    def parse_user_query(self, query: str) -> dict:
        """Parse the user query to extract topology requirements"""
        requirements = {
            "network_types": [],
            "node_counts": {},
            "connection_types": [],
            "security_requirements": [],
            "topology_structure": None
        }
        
        # Convert query to lowercase for easier matching
        query_lower = query.lower()
        
        # Extract network types
        if "classical network" in query_lower:
            requirements["network_types"].append("CLASSICAL_NETWORK")
        if "quantum network" in query_lower:
            requirements["network_types"].append("QUANTUM_NETWORK")
            # If we detect a quantum network, we should look for quantum hosts
            # Look for explicit number of quantum hosts
            matches = re.findall(r"(\d+)\s*quantum\s*hosts?", query_lower)
            if matches:
                requirements["node_counts"][NodeType.QUANTUM_HOST] = int(matches[0])
            # If no explicit number but quantum network is mentioned with hosts
            elif "quantum" in query_lower and "host" in query_lower:
                # Try to find any number mentioned
                number_match = re.findall(r"(\d+)", query_lower)
                if number_match:
                    requirements["node_counts"][NodeType.QUANTUM_HOST] = int(number_match[0])
                
        if "hybrid network" in query_lower or \
           (("classical" in query_lower or "quantum" in query_lower) and "hybrid" in query_lower):
            requirements["network_types"].append("HYBRID_NETWORK")
        
        # Extract connection types
        if "classical link" in query_lower:
            requirements["connection_types"].append("CLASSICAL_LINK")
        if "quantum channel" in query_lower:
            requirements["connection_types"].append("QUANTUM_CHANNEL")
        if "hybrid link" in query_lower:
            requirements["connection_types"].append("HYBRID_LINK")
        
        # Extract node counts using regex
        number_words = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
        }
        
        # Convert number words to digits
        for word, digit in number_words.items():
            query_lower = query_lower.replace(word, str(digit))
        
        # Extract node counts
        node_patterns = [
            (r"(\d+)\s*(?:classical\s*)?hosts?", NodeType.CLIENT),
            (r"(\d+)\s*(?:classical\s*)?routers?", NodeType.CLASSICAL_ROUTER),
            (r"(\d+)\s*quantum\s*hosts?", NodeType.QUANTUM_HOST),
            (r"(\d+)\s*quantum\s*adapters?", NodeType.QUANTUM_ADAPTER)
        ]
        
        for pattern, node_type in node_patterns:
            matches = re.findall(pattern, query_lower)
            if matches:
                requirements["node_counts"][node_type] = int(matches[0])
        
        # Extract security requirements
        if "secure" in query_lower:
            requirements["security_requirements"].append("SECURE")
        if "quantum key distribution" in query_lower or "qkd" in query_lower:
            requirements["security_requirements"].append("QKD")
        
        # Extract topology structure
        if "mesh" in query_lower:
            requirements["topology_structure"] = "MESH"
        elif "star" in query_lower:
            requirements["topology_structure"] = "STAR"
        elif "ring" in query_lower:
            requirements["topology_structure"] = "RING"
        elif "bus" in query_lower:
            requirements["topology_structure"] = "BUS"
        
        # Add default connection types based on network types
        if "CLASSICAL_NETWORK" in requirements["network_types"] and "CLASSICAL_LINK" not in requirements["connection_types"]:
            requirements["connection_types"].append("CLASSICAL_LINK")
        if "QUANTUM_NETWORK" in requirements["network_types"] and "QUANTUM_CHANNEL" not in requirements["connection_types"]:
            requirements["connection_types"].append("QUANTUM_CHANNEL")
        if "HYBRID_NETWORK" in requirements["network_types"] and "HYBRID_LINK" not in requirements["connection_types"]:
            requirements["connection_types"].append("HYBRID_LINK")
        
        return requirements

    def _validate_network_types(self, topology: dict, requirements: dict) -> tuple[list[str], list[str]]:
        issues = []
        recommendations = []
        
        required_types = set(requirements.get("network_types", []))
        found_types = set()
        
        for zone in topology.get("zones", []):
            for network in zone.get("networks", []):
                network_type = network.get("type")
                if network_type:
                    found_types.add(network_type)
        
        # Special handling for hybrid networks
        if "HYBRID_NETWORK" in required_types:
            if "CLASSICAL_NETWORK" in found_types and "QUANTUM_NETWORK" in found_types:
                found_types.add("HYBRID_NETWORK")
        
        for req_type in required_types:
            if req_type not in found_types:
                issues.append(f"Missing required network type: {req_type}")
                recommendations.append("Add missing network types or modify existing ones")
        
        return issues, recommendations

    def _get_node_type(self, topology: dict, node_name: str) -> NodeType:
        """Get the type of a node by its name"""
        for zone in topology.get("zones", []):
            for network in zone.get("networks", []):
                for host in network.get("hosts", []):
                    if host.get("name") == node_name:
                        node_type = host.get("type", "").upper().replace("QUANTUMHOST", "QUANTUM_HOST")
                        if node_type == "CLIENT":
                            return NodeType.CLIENT
                        elif node_type == "CLASSICAL_ROUTER":
                            return NodeType.CLASSICAL_ROUTER
                        elif node_type == "QUANTUM_HOST":
                            return NodeType.QUANTUM_HOST
                        elif node_type == "QUANTUM_ADAPTER":
                            return NodeType.QUANTUM_ADAPTER
            
            # Check adapters
            for adapter in zone.get("adapters", []):
                if adapter.get("name") == node_name:
                    return NodeType.QUANTUM_ADAPTER
        
        return None

    def _validate_node_counts(self, topology: dict, requirements: dict) -> tuple[list[str], list[str]]:
        issues = []
        recommendations = []
        
        required_counts = requirements.get("node_counts", {})
        found_counts = {
            NodeType.CLIENT: 0,
            NodeType.CLASSICAL_ROUTER: 0,
            NodeType.QUANTUM_HOST: 0,
            NodeType.QUANTUM_ADAPTER: 0
        }
        
        # Count nodes in topology
        for zone in topology.get("zones", []):
            for network in zone.get("networks", []):
                for host in network.get("hosts", []):
                    node_type = host.get("type", "").upper().replace("QUANTUMHOST", "QUANTUM_HOST")
                    if node_type == "CLIENT":
                        found_counts[NodeType.CLIENT] += 1
                    elif node_type == "CLASSICAL_ROUTER":
                        found_counts[NodeType.CLASSICAL_ROUTER] += 1
                    elif node_type == "QUANTUM_HOST":
                        found_counts[NodeType.QUANTUM_HOST] += 1
            
            # Count adapters
            for adapter in zone.get("adapters", []):
                found_counts[NodeType.QUANTUM_ADAPTER] += 1
        
        # Compare counts
        for node_type, required_count in required_counts.items():
            found_count = found_counts.get(node_type, 0)
            if found_count < required_count:
                issues.append(f"Missing {required_count - found_count} {node_type.name} nodes")
                recommendations.append(f"Add {required_count - found_count} {node_type.name} nodes")
            elif found_count > required_count:
                issues.append(f"Extra {found_count - required_count} {node_type.name} nodes")
                recommendations.append(f"Remove {found_count - required_count} {node_type.name} nodes")
        
        return issues, recommendations

    def _validate_connections(self, topology: dict, requirements: dict) -> tuple[list[str], list[str]]:
        issues = []
        recommendations = []
        
        # Get all connections from the topology
        all_connections = []
        for zone in topology.get("zones", []):
            for network in zone.get("networks", []):
                for conn in network.get("connections", []):
                    all_connections.append((conn["from_node"], conn["to_node"]))
        
        # Track adapter connections and their specifications
        adapter_specs = {}  # adapter_name -> {"classical_host": str, "quantum_host": str}
        adapter_connections = {}  # adapter_name -> {"classical": [], "quantum": []}
        
        # Initialize adapter tracking from topology specification
        for zone in topology.get("zones", []):
            for adapter in zone.get("adapters", []):
                adapter_name = adapter["name"]
                adapter_specs[adapter_name] = {
                    "classical_host": adapter["classicalHost"],
                    "quantum_host": adapter["quantumHost"],
                    "classical_network": adapter["classicalNetwork"],
                    "quantum_network": adapter["quantumNetwork"]
                }
                adapter_connections[adapter_name] = {
                    "classical": [],
                    "quantum": [],
                    "classical_network": adapter["classicalNetwork"],
                    "quantum_network": adapter["quantumNetwork"]
                }
        
        # Validate connections based on node types and network context
        for zone in topology.get("zones", []):
            for network in zone.get("networks", []):
                network_type = network.get("type")
                network_name = network.get("name")
                
                for conn in network.get("connections", []):
                    from_node = self._get_node_type(topology, conn["from_node"])
                    to_node = self._get_node_type(topology, conn["to_node"])
                    
                    if not from_node or not to_node:
                        issues.append(f"Invalid node type for connection between {conn['from_node']} and {conn['to_node']}")
                        continue
                    
                    # Track and validate adapter connections
                    if from_node == NodeType.QUANTUM_ADAPTER or to_node == NodeType.QUANTUM_ADAPTER:
                        adapter_name = conn["from_node"] if from_node == NodeType.QUANTUM_ADAPTER else conn["to_node"]
                        other_node = conn["to_node"] if from_node == NodeType.QUANTUM_ADAPTER else conn["from_node"]
                        other_node_type = to_node if from_node == NodeType.QUANTUM_ADAPTER else from_node
                        
                        # Verify adapter exists in topology specification
                        if adapter_name not in adapter_specs:
                            issues.append(f"Adapter {adapter_name} not found in topology specification")
                            recommendations.append(f"Add adapter {adapter_name} to topology specification")
                            continue
                        
                        # Track the connection based on node type
                        if other_node_type in [NodeType.CLIENT, NodeType.CLASSICAL_ROUTER]:
                            adapter_connections[adapter_name]["classical"].append(other_node)
                            # Verify connection is in the correct network
                            if network_name != adapter_specs[adapter_name]["classical_network"]:
                                issues.append(f"Adapter {adapter_name} connected to classical node in wrong network")
                                recommendations.append(f"Move connection to {adapter_specs[adapter_name]['classical_network']}")
                        elif other_node_type == NodeType.QUANTUM_HOST:
                            adapter_connections[adapter_name]["quantum"].append(other_node)
                            # Verify connection is in the correct network
                            if network_name != adapter_specs[adapter_name]["quantum_network"]:
                                issues.append(f"Adapter {adapter_name} connected to quantum node in wrong network")
                                recommendations.append(f"Move connection to {adapter_specs[adapter_name]['quantum_network']}")
                        else:
                            issues.append(f"Invalid connection type for adapter {adapter_name}")
                            recommendations.append("Adapters should only connect to classical or quantum nodes")
                    
                    # Validate connections based on network type and node types
                    if network_type == "CLASSICAL_NETWORK":
                        # Classical network should only have classical connections
                        if from_node == NodeType.QUANTUM_HOST or to_node == NodeType.QUANTUM_HOST:
                            issues.append(f"Invalid quantum node in classical network: {conn['from_node']} to {conn['to_node']}")
                            recommendations.append("Move quantum nodes to quantum network")
                        elif from_node in [NodeType.CLIENT, NodeType.CLASSICAL_ROUTER] and \
                             to_node in [NodeType.CLIENT, NodeType.CLASSICAL_ROUTER]:
                            # Check if CLASSICAL_LINK is required
                            if "CLASSICAL_LINK" in requirements.get("connection_types", []):
                                if conn.get("noise_model") != "default":
                                    issues.append(f"Invalid noise model for classical link between {conn['from_node']} and {conn['to_node']}")
                                    recommendations.append("Use default noise model for classical links")
                    
                    elif network_type == "QUANTUM_NETWORK":
                        # Quantum network should only have quantum connections
                        if from_node in [NodeType.CLIENT, NodeType.CLASSICAL_ROUTER] or \
                           to_node in [NodeType.CLIENT, NodeType.CLASSICAL_ROUTER]:
                            issues.append(f"Invalid classical node in quantum network: {conn['from_node']} to {conn['to_node']}")
                            recommendations.append("Move classical nodes to classical network")
                        elif from_node == NodeType.QUANTUM_HOST and to_node == NodeType.QUANTUM_HOST:
                            # Check if QUANTUM_CHANNEL is required
                            if "QUANTUM_CHANNEL" in requirements.get("connection_types", []):
                                if conn.get("noise_model") != "quantum":
                                    issues.append(f"Invalid noise model for quantum channel between {conn['from_node']} and {conn['to_node']}")
                                    recommendations.append("Use quantum noise model for quantum channels")
        
        # Validate adapter connections are complete and match specifications
        for adapter_name, connections in adapter_connections.items():
            if adapter_name not in adapter_specs:
                continue
                
            # Check classical connection
            if not any(host == adapter_specs[adapter_name]["classical_host"] for host in connections["classical"]):
                issues.append(f"Adapter {adapter_name} missing connection to specified classical host {adapter_specs[adapter_name]['classical_host']}")
                recommendations.append(f"Add connection between {adapter_name} and {adapter_specs[adapter_name]['classical_host']}")
            
            # Check quantum connection
            if not any(host == adapter_specs[adapter_name]["quantum_host"] for host in connections["quantum"]):
                issues.append(f"Adapter {adapter_name} missing connection to specified quantum host {adapter_specs[adapter_name]['quantum_host']}")
                recommendations.append(f"Add connection between {adapter_name} and {adapter_specs[adapter_name]['quantum_host']}")
            
            # Check for extra connections
            if len(connections["classical"]) > 1:
                issues.append(f"Adapter {adapter_name} has too many classical connections")
                recommendations.append("Adapters should only connect to one classical host")
            
            if len(connections["quantum"]) > 1:
                issues.append(f"Adapter {adapter_name} has too many quantum connections")
                recommendations.append("Adapters should only connect to one quantum host")
        
        # Check for required connections
        if "connections" in requirements:
            for req_conn in requirements["connections"]:
                from_node, to_node = req_conn
                found = False
                for conn in all_connections:
                    if (conn[0] == from_node and conn[1] == to_node) or \
                       (conn[0] == to_node and conn[1] == from_node):
                        found = True
                        break
                
                if not found:
                    issues.append(f"Missing required connection between {from_node} and {to_node}")
                    recommendations.append(f"Add connection between {from_node} and {to_node}")
        
        return issues, recommendations

    def _validate_security(self, topology: dict, requirements: dict) -> tuple[list[str], list[str]]:
        issues = []
        recommendations = []
        
        security_reqs = requirements.get("security_requirements", [])
        
        # Check for QKD requirement
        if "QKD" in security_reqs:
            has_qkd = False
            for zone in topology.get("zones", []):
                for network in zone.get("networks", []):
                    if network.get("type") == "QUANTUM_NETWORK":
                        has_qkd = True
                        break
            
            if not has_qkd:
                issues.append("Missing quantum network for QKD")
                recommendations.append("Add quantum network for QKD support")
        
        # Check for secure zones
        if "SECURE" in security_reqs:
            for zone in topology.get("zones", []):
                if zone.get("type") != "SECURE":
                    issues.append(f"Zone {zone.get('name')} is not marked as secure")
                    recommendations.append(f"Mark zone {zone.get('name')} as secure")
        
        return issues, recommendations

    def _calculate_confidence_score(self, issues: List[str]) -> float:
        """Calculate a confidence score based on the number and severity of issues"""
        if not issues:
            return 1.0
        
        # Weight different types of issues
        weights = {
            "Missing required network type": 0.3,
            "Missing required node": 0.2,
            "Missing required connection": 0.2,
            "Missing quantum network for QKD": 0.3,
            "Missing central node": 0.2,
            "Insufficient connections": 0.1
        }
        
        total_weight = 0.0
        for issue in issues:
            for key, weight in weights.items():
                if key in issue:
                    total_weight += weight
                    break
        
        return max(0.0, 1.0 - total_weight) 