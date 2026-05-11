# venti-telemetry-analysis

**Version:** 1.0.0
**Author:** Venti Technologies, AI Platform
**Compatible with:** Claude Code, Codex, OpenCode

A skill for tasks involving vehicle telemetry data: ingestion pipeline code, schema validation, time-series queries, data quality checks, and fleet analytics. Gives the agent the domain context it needs to reason correctly about AV sensor data without requiring the assigning engineer to re-explain the domain every time.

---

## When to use this skill

Use this skill when an issue involves:

- Writing or improving a telemetry ingestion or processing pipeline
- Validating, cleaning, or transforming sensor data records
- Writing queries against time-series data (InfluxDB, TimescaleDB, or similar)
- Diagnosing data quality problems (dropped fields, out-of-order records, duplicates)
- Building or reviewing fleet status dashboards or aggregation jobs
- Performance profiling of data pipeline code

Trigger phrases: "telemetry", "sensor data", "fleet data", "time-series", "ingestion pipeline", "data pipeline", "GPS records", "speed data", "CAN bus", "vehicle data".

---

## Domain context: Venti's telemetry architecture

Understanding this context will help you reason correctly about any telemetry task.

**Data sources:** Each autonomous vehicle emits sensor telemetry at high frequency, typically 10–100 Hz depending on the sensor. Sources include: GPS/GNSS (position, heading, speed), LIDAR point clouds (obstacle detection), camera frames (object classification), CAN bus (brake status, steering angle, motor torque), IMU (acceleration, gyroscope).

**Data pipeline shape:**
```
Vehicle (sensors)
  → Edge buffer (on-board aggregation, handles network dropouts)
  → Message broker (high-throughput queue, e.g. Kafka or MQTT)
  → Stream processor (real-time transformation and validation)
  → Time-series database (InfluxDB or TimescaleDB for queryable history)
  → Object storage (S3-compatible for raw frame archival)
  → Fleet dashboard / analytics layer
```

**Common telemetry record schema:**
```python
{
    "vehicle_id":  str,          # e.g. "VNT-042"
    "sensor_id":   str,          # e.g. "GPS-primary"
    "timestamp":   int,          # Unix epoch milliseconds (UTC)
    "sequence":    int,          # Monotonically increasing per vehicle per session
    "speed_mps":   float,        # Metres per second (NOT km/h)
    "heading_deg": float,        # 0–360, clockwise from north
    "lat":         float,        # WGS84 latitude
    "lon":         float,        # WGS84 longitude
    "alt_m":       float,        # Altitude in metres
    "quality":     int,          # GPS fix quality (0=no fix, 1=GPS, 2=DGPS, 4=RTK)
}
```

**Known failure modes to watch for:**
- **Field dropout:** Vehicles occasionally emit partial records when a sensor disconnects. Never assume all fields are present.
- **Out-of-order delivery:** Network latency means records may arrive out of sequence. Do not assume `timestamp` order equals arrival order.
- **GPS quality degradation:** In tunnels or dense urban environments, `quality` drops to 0. Downstream code must handle `quality == 0` without crashing.
- **Duplicate records:** The edge buffer retries on delivery failure. Deduplication by `(vehicle_id, sensor_id, sequence)` is the correct approach, not by timestamp alone (timestamps can repeat at high frequency).
- **Unit confusion:** `speed_mps` is metres per second. Do not confuse with km/h or mph. State units explicitly in variable names and comments.

---

## Task execution process

### For pipeline and processing tasks:

1. **Understand the data flow.** Before writing any code, identify where in the pipeline this task sits. Is it ingestion, transformation, storage, or query? Name this at the start of your work.

2. **Write defensively.** Use `.get()` with defaults for all dict accesses. Validate critical fields (`vehicle_id`, `timestamp`, `sequence`) before processing. Log and skip (don't crash) on invalid records.

3. **Type everything.** Use `TypedDict` or `dataclass` for record schemas. Name your types clearly: `TelemetryRecord`, `ProcessedRecord`, `FleetSummary`.

4. **Include observability.** Log at the start and end of batch processing. Log the count of records processed, skipped, and errored. Use structured logging (key=value pairs) not f-strings.

5. **Write tests.** Every telemetry function needs at minimum: a happy path test, a test with missing optional fields, a test with a completely invalid record, and a performance test with a large batch (≥1000 records).

### For query and analytics tasks:

1. Prefer parameterised queries over string formatting. Never interpolate user input or vehicle IDs directly into query strings.
2. For time-series queries, always filter by time range first (the most selective filter in a time-series DB). Avoid full-table scans.
3. For aggregation queries, specify the time bucket explicitly. Do not rely on default behaviour.

### For data quality / debugging tasks:

1. Start by understanding what "correct" looks like. Get or define the expected schema before analysing deviations.
2. Report findings as structured output: total records examined, count of each anomaly type, example record for each anomaly, suggested fix.

---

## Output standards

When delivering code for telemetry tasks:

```python
# Always include:
import logging
from typing import TypedDict

logger = logging.getLogger(__name__)

class TelemetryRecord(TypedDict):
    vehicle_id:  str
    sensor_id:   str
    timestamp:   int
    sequence:    int
    speed_mps:   float
    # ... other fields

def process_batch(batch: list[dict]) -> list[TelemetryRecord]:
    """
    Process a batch of raw telemetry records.

    Args:
        batch: Raw records from the stream processor.
               Records may have missing or malformed fields.

    Returns:
        List of validated and normalised TelemetryRecord dicts.
        Invalid records are logged and skipped, never raised.
    """
    processed = []
    skipped   = 0

    for record in batch:
        try:
            # validation logic here
            processed.append(validated_record)
        except (KeyError, TypeError, ValueError) as e:
            logger.warning(
                "skipped_invalid_record",
                vehicle_id=record.get("vehicle_id", "unknown"),
                error=str(e),
            )
            skipped += 1

    logger.info(
        "batch_processed",
        total=len(batch),
        processed=len(processed),
        skipped=skipped,
    )
    return processed
```

---

## Notes

- Speed is always in **metres per second** (speed_mps). Never assume km/h.
- Timestamps are always **Unix epoch milliseconds** (not seconds, not ISO strings).
- Deduplication key is always **(vehicle_id, sensor_id, sequence)**.
- If a task involves raw LIDAR or camera data (binary / point cloud formats), flag it and ask for clarification before writing code. These have separate handling pipelines.

---

## CHANGELOG

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | May 2026 | Initial version. Telemetry record schema, seven failure modes, processing templates, output standards. |
