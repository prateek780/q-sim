#!/usr/bin/env python3
"""
Script to retrieve ReJSON-type logs from Redis and store them in a JSON file.
This script handles Redis databases that store logs using ReJSON module.
"""

import json
import redis
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("rejson_log_retriever")

# Redis connection details
REDIS_HOST = "redis-11509.c90.us-east-1-3.ec2.redns.redis-cloud.com"
REDIS_PORT = 11509
REDIS_USERNAME = "default"
REDIS_PASSWORD = "aDevCXKeLli9kldGJccV15D1yS93Oyvd"
REDIS_DB = 0
REDIS_SSL = False

def get_rejson_data(redis_conn, key):
    """
    Try multiple approaches to retrieve ReJSON data
    
    Args:
        redis_conn: Redis connection
        key: Redis key to retrieve
        
    Returns:
        The data or None if unable to retrieve
    """
    try:
        # First attempt: Try Redis JSON.GET if redis-py has the json() method
        if hasattr(redis_conn, 'json'):
            try:
                return redis_conn.json().get(key)
            except Exception:
                pass
        
        # Second attempt: Use regular get and parse JSON
        try:
            raw_data = redis_conn.get(key)
            if raw_data:
                return json.loads(raw_data)
        except Exception:
            pass
            
        # Third attempt: Use hgetall
        try:
            hash_data = redis_conn.hgetall(key)
            if hash_data:
                return hash_data
        except Exception:
            pass
            
        # Fourth attempt: Execute raw command
        try:
            result = redis_conn.execute_command('JSON.GET', key)
            if result:
                return json.loads(result)
        except Exception:
            pass
            
        # Last attempt: Try dumping the key and parsing
        try:
            dump_data = redis_conn.dump(key)
            if dump_data:
                return {"_raw_dump": str(dump_data)}
        except Exception:
            pass
            
        return None
    except Exception as e:
        logger.error(f"All methods failed to retrieve data for key {key}: {e}")
        return None

def retrieve_logs(pattern="network-sim:log:*", output_file="rejson_logs.json", batch_size=100):
    """
    Retrieve ReJSON logs from Redis and store them in a JSON file
    
    Args:
        pattern: Redis key pattern to match log entries
        output_file: File to save the logs to
        batch_size: Number of keys to retrieve in each batch
    """
    # Connect to Redis
    logger.info(f"Connecting to Redis: {REDIS_HOST}:{REDIS_PORT}")
    redis_conn = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        username=REDIS_USERNAME,
        password=REDIS_PASSWORD,
        db=REDIS_DB,
        ssl=REDIS_SSL,
        decode_responses=True
    )
    
    try:
        # Test connection
        if redis_conn.ping():
            logger.info("Connected to Redis successfully")
        else:
            logger.error("Failed to connect to Redis")
            return
    except Exception as e:
        logger.error(f"Error connecting to Redis: {e}")
        return
    
    # Get all keys matching the pattern
    logger.info(f"Scanning for keys matching pattern: {pattern}")
    all_logs = {}
    cursor = 0
    keys = []
    
    while True:
        cursor, batch = redis_conn.scan(cursor=cursor, match=pattern, count=batch_size)
        keys.extend(batch)
        
        if cursor == 0:
            break
    
    total_keys = len(keys)
    logger.info(f"Found {total_keys} keys matching the pattern")
    
    # Process each key
    for i, key in enumerate(keys):
        try:
            key_type = redis_conn.type(key)
            logger.info(f"Processing key {i+1}/{total_keys}: {key} (Type: {key_type})")
            
            # Extract the log ID from the key for easier identification
            log_id = key.split(":")[-1] if ":" in key else key
            
            # Try to get data using appropriate method based on key type
            if key_type == "ReJSON-RL":
                data = get_rejson_data(redis_conn, key)
                if data:
                    all_logs[log_id] = data
                else:
                    all_logs[log_id] = {"error": "Unable to retrieve ReJSON data"}
            elif key_type == "string":
                raw_data = redis_conn.get(key)
                try:
                    all_logs[log_id] = json.loads(raw_data)
                except json.JSONDecodeError:
                    all_logs[log_id] = {"raw_text": raw_data}
            elif key_type == "hash":
                all_logs[log_id] = redis_conn.hgetall(key)
            else:
                logger.warning(f"Skipping key with type {key_type}: {key}")
                continue
            
        except Exception as e:
            logger.error(f"Error processing key {key}: {e}")
            all_logs[log_id] = {"error": str(e)}
    
    # Save logs to file
    output_data = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_keys": total_keys,
            "pattern": pattern
        },
        "logs": all_logs
    }
    
    logger.info(f"Saving {len(all_logs)} logs to file: {output_file}")
    try:
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"Successfully saved logs to {output_file}")
    except Exception as e:
        logger.error(f"Error saving logs to file: {e}")

def main():
    """Main function"""
    output_file = f"rejson_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    retrieve_logs(pattern="network-sim:log:*", output_file=output_file)
    print(f"\nLogs retrieved and saved to: {output_file}")

if __name__ == "__main__":
    main() 