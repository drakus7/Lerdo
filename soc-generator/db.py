import os
import clickhouse_connect

def get_client():
    host = os.getenv("CLICKHOUSE_HOST","localhost")
    port = int(os.getenv("CLICKHOUSE_PORT",8123))
    return clickhouse_connect.get_client(host=host, port=port, database="soc_dashboard",username="default",password="")
def insert_events(client, events_batch):
    """
    event_batch is a list of tuples: (timestamp, source_type, host, raw_payload)
    """
    if not events_batch:
        return
    client.insert('raw_events', events_batch, column_names=['timestamp','source_type','host','raw_payload'])
