"""Vector log model for storing embedded logs in Redis"""

import json
import logging
import traceback
import numpy as np
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from redis.commands.search.query import Query
from redis.commands.search.indexDefinition import IndexDefinition
from redis.commands.search.field import VectorField, TextField, NumericField, TagField

from core.enums import NodeType
from data.models.connection.redis import get_redis_conn
from data.models.simulation.log_model import LogEntryModel, LogLevel

# Constants for vector indexing
VECTOR_DIM =768  # Dimension for embedding vectors (e.g., OpenAI ada-002)
VECTOR_INDEX_NAME = "logs_vector_idx"
PREFIX = "simlog:vector:"


class VectorLogEntry:
    """Model for vector-embedded log entries"""
    logger = logging.getLogger(__name__)
    
    @staticmethod
    def create_index(redis_conn=None, recreate=False):
        """Create Redis search index for vector similarity search"""
        if redis_conn is None:
            redis_conn = get_redis_conn()

        # Define schema
        schema = (
            # Vector field for embeddings
            VectorField(
                "embedding",
                "HNSW",
                {"TYPE": "FLOAT32", "DIM": VECTOR_DIM, "DISTANCE_METRIC": "COSINE"},
            ),
            TextField("component"),
            # Numeric fields for filtering
            NumericField("timestamp", sortable=True),
            # Tag fields for exact match filtering
            TagField("simulation_id"),
            TagField("level"),
            TagField("entity_type", sortable=True),
            TagField("entity_id", sortable=True),
        )

        try:
            # Check if index exists and create if it doesn't
            indices = redis_conn.execute_command("FT._LIST")
            index_exists = VECTOR_INDEX_NAME in indices
                
            # Drop if requested and exists
            if recreate and index_exists:
                print("Dropping Index")
                redis_conn.execute_command(f"FT.DROPINDEX {VECTOR_INDEX_NAME}")
                index_exists = False

            if not index_exists or recreate:
                redis_conn.ft(VECTOR_INDEX_NAME).create_index(
                    schema,
                    definition=IndexDefinition(prefix=[PREFIX], language_field='language')
                )
                print(f"Created index {VECTOR_INDEX_NAME}")
        except Exception as e:
            print(f"Error creating index: {e}")

    @staticmethod
    def store_log_with_embedding(
        log_entry: Union[LogEntryModel, Dict], embedding: List[float], redis_conn=None
    ):
        """Store a log entry with its vector embedding"""
        if redis_conn is None:
            redis_conn = get_redis_conn()

        # Convert LogEntry to dict if needed
        if isinstance(log_entry, LogEntryModel):
            # Create a dictionary from LogEntry
            log_data = {
                "pk": log_entry.pk,
                "simulation_id": log_entry.simulation_id,
                "timestamp": log_entry.timestamp.timestamp(),
                "level": log_entry.level.value,
                "component": log_entry.component,
                "entity_type": (
                    log_entry.entity_type.value if log_entry.entity_type else None
                ),
                "entity_id": log_entry.entity_id,
                "details": json.dumps(log_entry.details),
            }
        else:
            # Input is already a dict
            log_data = log_entry.copy()
            # Convert timestamp to float if it's a datetime
            if isinstance(log_data.get("timestamp"), datetime):
                log_data["timestamp"] = log_data["timestamp"].timestamp()
            # Convert enums to values if needed
            if isinstance(log_data.get("level"), LogLevel):
                log_data["level"] = log_data["level"].value
            if isinstance(log_data.get("entity_type"), NodeType):
                log_data["entity_type"] = log_data["entity_type"].value
            # Convert details to string if it's a dict
            if isinstance(log_data.get("details"), dict):
                log_data["details"] = json.dumps(log_data["details"])

        # Convert embedding to the correct format (float32)
        embedding_np = np.array(embedding, dtype=np.float32).tobytes()

        # Generate a key
        key = f"{PREFIX}{log_data.get('pk', datetime.now().timestamp())}"

        # Prepare the hash data
        hash_data = {
            "embedding": embedding_np,
            **{k: v for k, v in log_data.items() if v is not None},
        }

        # Store in Redis
        redis_conn.hset(key, mapping=hash_data)
        return key

    @staticmethod
    def search_similar(
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        redis_conn=None,
    ) -> List[Dict[str, Any]]:
        """Search for logs similar to the given embedding"""
        if redis_conn is None:
            redis_conn = get_redis_conn()

        # Convert embedding to the correct format
        query_embedding_np = np.array(query_embedding, dtype=np.float32)

        # Build query
        base_query = f"=>[KNN {top_k} @embedding $embedding AS score]"

        # Apply filters if provided
        if filters:
            filter_parts = []

            # Handle simulation_id filter
            if "simulation_id" in filters:
                filter_parts.append(f"@simulation_id:{{{filters['simulation_id']}}}")

            # Handle level filter
            if "level" in filters:
                levels = filters["level"]
                if isinstance(levels, (list, tuple)):
                    level_parts = [f"{{{level}}}" for level in levels]
                    filter_parts.append(f"@level:({' | '.join(level_parts)})")
                else:
                    filter_parts.append(f"@level:{{{levels}}}")

            # Handle entity_type filter
            if "entity_type" in filters:
                filter_parts.append(f"@entity_type:{{{filters['entity_type']}}}")

            # Handle entity_id filter
            if "entity_id" in filters:
                filter_parts.append(f"@entity_id:{{{filters['entity_id']}}}")

            # Handle time range filter
            if "time_range" in filters:
                start, end = filters["time_range"]
                if isinstance(start, datetime):
                    start = start.timestamp()
                if isinstance(end, datetime):
                    end = end.timestamp()
                filter_parts.append(f"@timestamp:[{start} {end}]")

            # Combine all filters
            if filter_parts:
                base_query = f"{' '.join(filter_parts)} {base_query}"
        print(base_query)
        query = Query(base_query).dialect(2)
        params_dict = {"embedding": query_embedding_np.tobytes()}

        # Execute the query
        try:
            results = redis_conn.ft(VECTOR_INDEX_NAME).search(query, params_dict)

            # Process and return results
            processed_results = []
            for doc in results.docs:
                result = {
                    k: v for k, v in doc.__dict__.items() if not k.startswith("_")
                }

                # Convert timestamp back to datetime
                if "timestamp" in result and result["timestamp"]:
                    result["timestamp"] = datetime.fromtimestamp(
                        float(result["timestamp"])
                    )

                # Parse details if available
                if "details" in result and result["details"]:
                    try:
                        result["details"] = json.loads(result["details"])
                    except:
                        pass  # Keep as string if not valid JSON

                processed_results.append(result)

            return processed_results
        except Exception as e:
            print(f"Error searching vector logs: {e}")
            return []

    @staticmethod
    def get_by_simulation(
        simulation_id: str, limit: int = 100, redis_conn=None
    ) -> List[Dict[str, Any]]:
        """Get vector logs for a specific simulation"""
        if redis_conn is None:
            redis_conn = get_redis_conn()

        # Build query for exact match on simulation_id
        query_str = f"@simulation_id:{{{simulation_id}}}"
        query = Query(query_str).sort_by("timestamp", asc=False).paging(0, limit)
        try:
            results = redis_conn.ft(VECTOR_INDEX_NAME).search(query)
            # Process and return results
            processed_results = []
            for doc in results.docs:
                result = {
                    k: v for k, v in doc.__dict__.items() if not k.startswith("_")
                }

                # Convert timestamp back to datetime
                if "timestamp" in result and result["timestamp"]:
                    result["timestamp"] = str(datetime.fromtimestamp(
                        float(result["timestamp"])
                    ))

                # Parse details if available
                if "details" in result and result["details"]:
                    try:
                        result["details"] = json.loads(result["details"])
                    except:
                        pass  # Keep as string if not valid JSON

                # Remove embedding from result to save bandwidth
                if "embedding" in result:
                    del result["embedding"]

                processed_results.append(result)

            return processed_results
        except Exception as e:
            VectorLogEntry.logger.exception("Error getting simulation vector logs")
            return []
