#!/usr/bin/env python3
import json
import subprocess
import datetime
import sys
import os

def parse_duration(duration_str):
    unit = duration_str[-1].lower()
    value = int(duration_str[:-1])
    now = datetime.datetime.now()

    if unit == 'd':
        return (now - datetime.timedelta(days=value)).isoformat()
    elif unit == 'h':
        return (now - datetime.timedelta(hours=value)).isoformat()
    elif unit == 'm':
        return (now - datetime.timedelta(minutes=value)).isoformat()
    else:
        raise ValueError("Invalid unit. Use D (days), H (hours), M (minutes).")

def extract_logs(config_path):
    with open(config_path) as f:
        config = json.load(f)

    log_type = config.get("log_type", "")
    log_duration = config.get("log_duration", "")
    since_time = parse_duration(log_duration)

    cmd = ["journalctl", "-u", log_type, "--since", since_time, "--output=json"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logs = result.stdout.strip().split('\n')
        log_json = [json.loads(line) for line in logs if line.strip()]
        print(json.dumps(log_json, indent=2))
    except subprocess.CalledProcessError as err:
        print(f"Error running journalctl: {err}", file=sys.stderr)

def main():
    if len(sys.argv) != 3 or sys.argv[1] != "--config-file":
        print("Usage: ./plugin --config-file <config.json>")
        sys.exit(1)

    config_path = sys.argv[2]
    if not os.path.isfile(config_path):
        print("Config file does not exist.")
        sys.exit(1)

    extract_logs(config_path)

if __name__ == "__main__":
    main()

