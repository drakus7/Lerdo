import requests
import time
import clickhouse_connect

VECTOR_METRICS_URL = "https://localhost:9598/metrics"
CH_HOST = "localhost"

def parse_prometheus_metric(text:str,metric_name:str) -> float:
    """Extract a single metric-value from prometheus txt format"""
    for line in text.splitlines():
        if line.startwith(metric_name) and not line.startwith("#"):
            return float(line.split()[-1])
    return 0.0

def get_eps(prev_total,current_total,interval_sec=60):
    return (current_total - prev_total)/interval_sec

def main():
    client = clickhouse_connect.get_client(host=CH_HOST,database="soc_dashboard")
    prev_sent = 0.0

    print("Starting Pipeline Health Poller...")
    while True:
        try:
            resp = request.get(VECTOR_METRICS_URL,timeout=5)
            text = resp.text

            sent_total = parse_prometheus_metric(text,"component_sent_events_total")
            errors_total = parse_prometheus_metric(text, "component_errors_total")
            buffer_size = parse_prometheus_metric(text, "buffer_events")

            eps = get_eps(prev_total, sent_total)
            prev_sent = sent_total

            #lag - compare the newest event timestamp in Clickhouse against wall clock
            lag_result = client.query(
                "SELECT now() - max(timestamp) AS lag FROM raw_events"
            )
            lag_seconds = float(lag_result.result_rows[0][0]) if lag_result.result_rows and lag_result.result_rows[0][0] is not None else 0.0

            client.insert(
                "pipeline_health",
                [[time.time(), eps, lag_seconds, int(errors_total), int(buffer_size)]],
                column_names=["snapshot_time", "events_per_sec", "lag_seconds", "error_count", "buffer_size"],
            )
            print(f"EPS={eps:.1f} lag={lag_seconds.2f}s errors={int(errors_total)}")
        except Exception as e:
            print(f"Error polling metrics: {e}")

        time.sleep(60)
if __name__ == "__main__":
    main()