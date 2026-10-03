import time
import random
from db import get_client, insert_events
from modes.normal import generate_normal_event
from modes.brute_force import generate_brute_force_sequence
from modes.exfiltration import generate_exfiltration_sequence

def main(): 
    print("Starting SOC Synthetic Data Generator...")
    client = get_client()
    print("Successfully connected to ClickHouse.")

    events_per_sec = 20
    batch_interval = 1.0

    buffer = []
    last_flush = time.time()

    print(f"Target rate: ~{events_per_sec} events/sec. Press Ctrl+C to stop.")

    try: 
        while True:
            loop_start = time.time()

            roll = random.random()
            if roll < 0.02:
                attack_type = random.choice(["brute_force","exfiltration"])
                print(f"- Triggering attack simulation: {attack_type}")
                if attack_type == "brute_force":
                    buffer.extend(generate_brute_force_sequence())
                else: buffer.extend(generate_exfiltration_sequence())
            else:
                buffer.append(generate_normal_event())

            if time.time() - last_flush >= batch_interval or len(buffer) >= events_per_sec:
                if buffer:
                    insert_events(client, buffer)
                    buffer.clear()
                    last_flush = time.time()

            elapsed = time.time()
            sleep_time = (1.0 / events_per_sec) - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n Generator stopped. Flusing remaining events...")
        try:
            if buffer:
                insert_events(client, buffer)
        except Exception as e:
            print(f"Note: Could not flush final buffer on exit ({e})")
        print("Exited cleanly.")
if __name__ == "__main__":
    main()