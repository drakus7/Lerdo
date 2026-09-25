import json
import datetime

def generate_ids_log(timestamp: datetime.datetime, src_ip: str, dst_ip: str, signature: str) -> str:
    # Example Suricata JSON alert
    payload = {
        "timestamp": timestamp.isoformat(),
        "event_type": "alert",
        "src_ip": src_ip,
        "dest_ip": dst_ip,
        "alert": {
            "signature": signature
        }
    }
    return json.dumps(payload)
