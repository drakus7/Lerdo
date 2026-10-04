import os
import json

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../logs"))
LOG_FILE = os.path.join(LOG_DIR, "events.jsonl")

os.makedirs(LOG_DIR,exist_ok=True)
#just to ensure that the directory exist

def get_client():
    return None

def insert_events(client,events_batch):
# event_batch is a list of tuples, writes records as JSON lines for Vector to tail
    if not events_batch:
        return
    with open(LOG_FILE, "a") as f:
        for ts, source_type, host, raw_payload in events_batch:
            record = {
                "timestamp": ts.isoformat() if hasattr(ts, 'isoformat') else str(ts),
                "source_type": source_type,
                "host": host,
                "raw_payload": raw_payload
            }
            f.write(json.dumps(record) + "\n")