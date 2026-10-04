import requests
import time
import datetime
import clickhouse_connect

VECTOR_METRICS_URL = "http://localhost:9598/metrics"
CH_HOST = "localhost"

def parse_vector_metric(text: str, metric_name: str, component_id: str) -> float:
    """Extract a specific component metric value from Vector's Prometheus text format."""
    for line in text.splitlines():
        if line.startswith(metric_name) and f'component_id="{component_id}"' in line and not line.startswith("#"):
            try:
                return float(line.split()[-1])
            except ValueError:
                continue
    return 0.0

def get_eps(prev_total, current_total, interval_sec=60):
    return max(0.0, (current_total - prev_total) / interval_sec)

def main():
    client = clickhouse_connect.get_client(host=CH_HOST, database="soc_dashboard")
    prev_sent = 0.0

    print(" Starting Pipeline Health Poller...")

    while True:
        try:
            resp = requests.get(VECTOR_METRICS_URL, timeout=5)
            text = resp.text

            # Parse sent events and errors specifically for the ClickHouse sink
            sent_total = parse_vector_metric(text, "vector_component_sent_events_total", "clickhouse_raw_events")
            errors_total = parse_vector_metric(text, "vector_component_errors_total", "clickhouse_raw_events")
            buffer_size = parse_vector_metric(text, "vector_buffer_sent_events_total", "clickhouse_raw_events")

            eps = get_eps(prev_sent, sent_total)
            prev_sent = sent_total

            # Lag: compare newest event timestamp in ClickHouse against wall clock.
            lag_result = client.query(
                "SELECT now() - max(timestamp) AS lag FROM raw_events"
            )
            lag_seconds = float(lag_result.result_rows[0][0]) if lag_result.result_rows and lag_result.result_rows[0][0] is not None else 0.0

            # Use a datetime object for DateTime64 compatibility
            now_dt = datetime.datetime.now()

            client.insert(
                "pipeline_health",
                [[now_dt, eps, lag_seconds, int(errors_total), int(buffer_size)]],
                column_names=["snapshot_time", "events_per_sec", "lag_seconds", "error_count", "buffer_size"],
            )

            print(f"EPS={eps:.1f} | Lag={lag_seconds:.2f}s | Errors={int(errors_total)} | Total Sent={int(sent_total)}")
        except Exception as e:
            print(f"- Error polling metrics: {e}")

        time.sleep(60)

if __name__ == "__main__":
    main()