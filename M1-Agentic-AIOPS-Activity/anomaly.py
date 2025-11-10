import os
import re
from collections import Counter
from datetime import datetime, timedelta

# anomaly.py
# Detect bursts of ERROR logs in logs.txt (same folder).
# Groups errors within a 10-minute window. BURST_THRESHOLD = 3.


BURST_THRESHOLD = 3
WINDOW = timedelta(minutes=10)

LOGFILE = os.path.join(os.path.dirname(__file__), "logs.txt")
TIMESTAMP_RE = re.compile(r'(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})')

def parse_timestamp(line):
    m = TIMESTAMP_RE.search(line)
    if not m:
        return None
    s = m.group(1)
    try:
        # handles "YYYY-MM-DD HH:MM:SS" and "YYYY-MM-DDTHH:MM:SS"
        return datetime.fromisoformat(s)
    except ValueError:
        try:
            return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None

def extract_error_message(line):
    i = line.find("ERROR")
    if i == -1:
        return ""
    msg = line[i + len("ERROR"):].strip()
    return msg or line.strip()

def load_error_events(path):
    events = []
    if not os.path.exists(path):
        print(f"logs file not found: {path}")
        return events
    with open(path, "r", encoding="utf-8") as f:
        for ln in f:
            if "ERROR" not in ln:
                continue
            ts = parse_timestamp(ln)
            if ts is None:
                # skip lines without parseable timestamp
                continue
            msg = extract_error_message(ln)
            events.append((ts, msg))
    events.sort(key=lambda x: x[0])
    return events

def find_bursts(events):
    bursts = []
    if not events:
        return bursts
    cur_start = events[0][0]
    cur_end = events[0][0]
    cur_messages = [events[0][1]]
    for ts, msg in events[1:]:
        if ts - cur_start <= WINDOW:
            cur_end = ts
            cur_messages.append(msg)
        else:
            if len(cur_messages) >= BURST_THRESHOLD:
                bursts.append((cur_start, cur_end, list(cur_messages)))
            # start new burst
            cur_start = ts
            cur_end = ts
            cur_messages = [msg]
    # final burst
    if len(cur_messages) >= BURST_THRESHOLD:
        bursts.append((cur_start, cur_end, list(cur_messages)))
    return bursts

def print_bursts(bursts):
    if not bursts:
        print("No anomalous error bursts detected.")
        return
    for start, end, messages in bursts:
        cnt = len(messages)
        most_common, _ = Counter(messages).most_common(1)[0]
        print(f"Burst start: {start.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Burst end:   {end.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Errors:      {cnt}")
        print(f"Top error:   {most_common}")
        print("-" * 40)

def main():
    events = load_error_events(LOGFILE)
    bursts = find_bursts(events)
    print_bursts(bursts)

if __name__ == "__main__":
    main()