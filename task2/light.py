"""BRACU Mongol-Tori — Task 2: Status Light Telemetry.

Usage: python light.py mission_log.csv targets.csv
Prints time_s,light for each valid telemetry row.
"""
import csv
import math
import sys

EARTH_RADIUS_M = 6_371_000.0
ARRIVAL_DISTANCE_M = 3.0
MAX_ARRIVAL_SPEED_MPS = 0.5
GREEN_DURATION_S = 5.0


def haversine_m(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2)
    a = min(1.0, max(0.0, a))
    return 2.0 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def value(row, *names):
    fields = {str(k).strip().lower(): v for k, v in row.items() if k is not None}
    for name in names:
        result = fields.get(name.lower())
        if result is not None and str(result).strip():
            return str(result).strip()
    return None


def read_targets(path):
    targets = []
    with open(path, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            raise ValueError("targets.csv is empty or has no header")
        for line_number, row in enumerate(reader, start=2):
            try:
                lat = float(value(row, "lat", "latitude"))
                lon = float(value(row, "lon", "longitude", "long"))
            except (TypeError, ValueError):
                raise ValueError(f"Invalid target coordinates on line {line_number}")
            if not (math.isfinite(lat) and math.isfinite(lon)
                    and -90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError(f"Out-of-range target coordinates on line {line_number}")
            targets.append((lat, lon))
    if not targets:
        raise ValueError("No target coordinates found")
    return targets


def normal_light(mode):
    mode = mode.strip().upper()
    return "red" if mode == "AUTO" else "blue"


def process_log(log_path, targets):
    target_index = 0
    previous_position = None
    green_until = None

    with open(log_path, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            raise ValueError("Mission log is empty or has no header")
        for row in reader:
            try:
                raw_time, raw_mode = value(row, "time_s", "time", "timestamp"), value(row, "mode")
                if raw_time is None or raw_mode is None:
                    continue
                time_s = float(raw_time)
                if not math.isfinite(time_s):
                    continue
            except (TypeError, ValueError):
                continue

            mode = raw_mode.strip().upper()
            light = normal_light(mode)
            if green_until is not None and time_s >= green_until:
                green_until = None
                target_index += 1

            lat = lon = None
            try:
                raw_lat, raw_lon = value(row, "lat", "latitude"), value(row, "lon", "longitude", "long")
                if raw_lat is not None and raw_lon is not None:
                    candidate_lat, candidate_lon = float(raw_lat), float(raw_lon)
                    if (math.isfinite(candidate_lat) and math.isfinite(candidate_lon)
                            and -90 <= candidate_lat <= 90 and -180 <= candidate_lon <= 180):
                        lat, lon = candidate_lat, candidate_lon
            except (TypeError, ValueError):
                pass

            if green_until is not None and time_s < green_until:
                light = "green"
            elif (lat is not None and target_index < len(targets)
                  and mode == "AUTO" and previous_position is not None):
                prev_time, prev_lat, prev_lon = previous_position
                elapsed = time_s - prev_time
                if elapsed > 0:
                    speed = haversine_m(prev_lat, prev_lon, lat, lon) / elapsed
                    target_lat, target_lon = targets[target_index]
                    distance = haversine_m(lat, lon, target_lat, target_lon)
                    if distance <= ARRIVAL_DISTANCE_M and speed < MAX_ARRIVAL_SPEED_MPS:
                        light, green_until = "green", time_s + GREEN_DURATION_S

            print(f"{time_s:g},{light}")
            if lat is not None and (previous_position is None or time_s > previous_position[0]):
                previous_position = (time_s, lat, lon)


def main():
    if len(sys.argv) != 3:
        print("Usage: python light.py mission_log.csv targets.csv", file=sys.stderr)
        raise SystemExit(2)
    try:
        targets = read_targets(sys.argv[2])
        process_log(sys.argv[1], targets)
    except (OSError, csv.Error, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
