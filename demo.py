"""
Venti AI Platform -- Phoenix Tracing Demo
==========================================
Demonstrates Arize Phoenix capturing traces from Claude (Anthropic SDK) calls.

This script simulates a realistic three-step workflow from Venti's Data Software
& Services team:
  1. Review a telemetry batch processor for production issues
  2. Rewrite it to address the findings
  3. Generate a unit test suite for the improved version

All three calls run inside a single parent OpenTelemetry span, so Phoenix renders
them as a linked trace tree under one root rather than three disconnected traces.
The root span carries a Multica task ID attribute, demonstrating how to correlate
Phoenix traces back to specific Multica issues.

Prerequisites:
  1. Phoenix must be running:        make phoenix-up
  2. ANTHROPIC_API_KEY must be set in ../.env or in your environment

Usage:
  pip install -r requirements.txt
  python demo.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
PHOENIX_ENDPOINT  = os.environ.get("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:4317")
PHOENIX_PROJECT   = os.environ.get("PHOENIX_PROJECT_NAME", "venti-claude-code")

# Simulated Multica task ID. In a real Multica agent context, this is injected
# by the daemon as the environment variable MULTICA_TASK_ID at runtime.
MULTICA_TASK_ID   = os.environ.get("MULTICA_TASK_ID", "VNT-042")

if not ANTHROPIC_API_KEY:
    print("Error: ANTHROPIC_API_KEY is not set.")
    print("Add it to ../.env or export it in your shell.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 1. Register Phoenix as the OpenTelemetry trace collector.
#    Must happen before importing Anthropic or any instrumented library.
# ---------------------------------------------------------------------------
from phoenix.otel import register
from openinference.instrumentation.anthropic import AnthropicInstrumentor
from opentelemetry import trace

tracer_provider = register(
    project_name=PHOENIX_PROJECT,
    endpoint=PHOENIX_ENDPOINT,
)
AnthropicInstrumentor().instrument(tracer_provider=tracer_provider)

tracer = trace.get_tracer(__name__)

print(f"Phoenix tracer registered -- project: '{PHOENIX_PROJECT}'")
print(f"Traces will appear at: http://localhost:6006")
print()

# ---------------------------------------------------------------------------
# 2. Normal Anthropic SDK usage -- Phoenix instruments this transparently.
#    All three calls run inside a single parent span so they appear as a
#    linked trace tree in the Phoenix UI, not as three separate traces.
# ---------------------------------------------------------------------------
import anthropic

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

TELEMETRY_CODE = """\
def parse_telemetry_batch(batch):
    results = []
    for record in batch:
        speed     = record['speed']
        timestamp = record['timestamp']
        gps       = record['gps']
        sensor_id = record['sensor_id']
        results.append({
            'speed': speed,
            'ts':    timestamp,
            'pos':   gps,
            'id':    sensor_id,
        })
    return results
"""

# Open a parent span. All child spans created while this span is active become
# part of the same trace tree. Set Multica task metadata here so every span in
# the trace carries it -- this is how you correlate a Phoenix trace back to
# the Multica issue that triggered the agent run.
with tracer.start_as_current_span(f"agent-task:{MULTICA_TASK_ID}") as root_span:
    root_span.set_attribute("multica.task_id",   MULTICA_TASK_ID)
    root_span.set_attribute("multica.agent",     "venti-reviewer")
    root_span.set_attribute("multica.workspace", "venti-data-services")

    # -----------------------------------------------------------------------
    # Task 1: Code review
    # -----------------------------------------------------------------------
    print("=" * 60)
    print("Task 1: Code review -- telemetry batch parser")
    print("=" * 60)

    try:
        response_1 = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=(
                "You are a senior software engineer at Venti Technologies, "
                "an autonomous vehicle company. You review code for safety-critical "
                "data pipelines that process real-time sensor telemetry from AV fleets. "
                "Your reviews are concise, specific, and production-focused. "
                "Always use the [MUST FIX] / [SHOULD FIX] / [CONSIDER] label format."
            ),
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Review this telemetry batch processor for production readiness.\n"
                        f"Focus on: missing-field handling, type validation, and "
                        f"performance at 10,000+ records/sec.\n\n"
                        f"```python\n{TELEMETRY_CODE}\n```"
                    ),
                }
            ],
        )
        review_output = response_1.content[0].text
        print(review_output)
        print()
    except Exception as e:
        print(f"Task 1 failed: {e}")
        review_output = None

    # -----------------------------------------------------------------------
    # Task 2: Rewrite based on the review findings
    # Uses Task 1 output directly -- this is a genuine chained workflow,
    # not three independent calls.
    # -----------------------------------------------------------------------
    print("=" * 60)
    print("Task 2: Rewrite to address review findings")
    print("=" * 60)

    try:
        review_context = (
            f"A senior engineer reviewed the code and identified these issues:\n\n"
            f"{review_output}\n\n" if review_output
            else ""
        )
        response_2 = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            system=(
                "You are a senior software engineer at Venti Technologies. "
                "Write clean, production-grade Python. "
                "Include type hints, structured logging, and error handling "
                "appropriate for safety-critical AV software. "
                "Return only the rewritten Python code, no explanation."
            ),
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Here is the original telemetry batch processor:\n\n"
                        f"```python\n{TELEMETRY_CODE}\n```\n\n"
                        f"{review_context}"
                        f"Rewrite the function to address all [MUST FIX] and "
                        f"[SHOULD FIX] items. Handle missing fields gracefully, "
                        f"add type hints, and include a docstring."
                    ),
                }
            ],
        )
        improved_code = response_2.content[0].text
        print(improved_code)
        print()
    except Exception as e:
        print(f"Task 2 failed: {e}")
        improved_code = TELEMETRY_CODE  # fall back to original for Task 3

    # -----------------------------------------------------------------------
    # Task 3: Generate unit tests for the improved implementation
    # Uses Task 2 output -- the tests are written against the rewritten code.
    # -----------------------------------------------------------------------
    print("=" * 60)
    print("Task 3: Generate unit tests for the improved implementation")
    print("=" * 60)

    try:
        response_3 = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1200,
            system=(
                "You are a senior software engineer at Venti Technologies. "
                "Write pytest unit tests. Be thorough with edge cases. "
                "Keep tests focused and fast. "
                "Return only the test file, no explanation."
            ),
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Write a pytest unit test file for this production "
                        f"telemetry batch parser:\n\n"
                        f"```python\n{improved_code}\n```\n\n"
                        f"Cover: happy path, missing required fields, invalid types, "
                        f"empty batch, out-of-order delivery, and large batch "
                        f"performance (1000+ records)."
                    ),
                }
            ],
        )
        print(response_3.content[0].text)
        print()
    except Exception as e:
        print(f"Task 3 failed: {e}")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("=" * 60)
print("Demo complete.")
print()
print("1 trace (3 child spans) sent to Phoenix. View at:")
print("  http://localhost:6006")
print()
print("In the Phoenix UI, under this trace you will see:")
print("  - Root span: agent-task:VNT-042")
print("      multica.task_id = VNT-042")
print("      multica.agent   = venti-reviewer")
print("  - Child span 1: code review call (prompt, response, tokens, latency)")
print("  - Child span 2: rewrite call (uses review findings as context)")
print("  - Child span 3: test generation call (uses rewritten code as context)")
print()
print("This is how a Multica agent task maps to a single traceable unit")
print("in Phoenix, with all AI calls linked under one root span.")
print("=" * 60)
