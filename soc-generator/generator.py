import time
import random
import argparse
from db import get_client, insert_events
from modes.normal import generate_normal_event
from modes.brute_force import generate_brute_force_sequence
from modes.exfiltration import generate_exfiltration_sequence

def main():
    # Set up command-line arguments
    parser = argparse.ArgumentParser(description="SOC Synthetic Data Generator")
    parser.add_argument(
        "--replay-speed", 
        type=float, 
        default=1.0, 
        help="Multiplier for event generation speed (e.g., 0.5 for slower, 2.0 for faster)"
    )
    parser.add_argument(
        "--base-rate", 
        type=int, 
        default=20, 
        help="Base events per second"
    )
    args = parser.parse_args()

    # Calculate target rate based on replay speed multiplier
    events_per_sec = max(1, int(args.base_rate * args.replay_speed))

    print("Starting SOC Synthetic Data Generator...")
    client = get_client()
    print("Successfully connected to ClickHouse.")

    batch_interval = 1.0  # Flush buffer every 1 second
    buffer = []
    last_flush = time.time()

    print(f"Target rate: ~{events_per_sec} events/sec (Speed multiplier: {args.replay_speed}x). Press Ctrl+C to stop.")

    try:
        while True:
            loop_start = time.time()

            # Probabilistically trigger attack sequences (2% chance per loop cycle)
            roll = random.random()
            if roll < 0.02:
                attack_type = random.choice(["brute_force", "exfiltration"])
                print(f"- Triggering attack simulation: {attack_type}")
                if attack_type == "brute_force":
                    buffer.extend(generate_brute_force_sequence())
                else:
                    buffer.extend(generate_exfiltration_sequence())
            else:
                buffer.append(generate_normal_event())

            # Batch flush to ClickHouse
            if time.time() - last_flush >= batch_interval or len(buffer) >= events_per_sec:
                if buffer:
                    insert_events(client, buffer)
                    buffer.clear()
                    last_flush = time.time()

            # Rate limiting sleep
            elapsed = time.time() - loop_start
            sleep_time = (1.0 / events_per_sec) - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\nGenerator stopped. Flushing remaining events...")
        try:
            if buffer:
                insert_events(client, buffer)
        except Exception as e:
            print(f"Note: Could not flush final buffer on exit ({e})")
        print("Exited cleanly.")

if __name__ == "__main__":
    main()