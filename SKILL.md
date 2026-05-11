# venti-code-review

**Version:** 1.0.0
**Author:** Venti Technologies, AI Platform
**Compatible with:** Claude Code, Codex, OpenCode

A shared code review skill for Venti engineering teams. Ensures every agent-assisted review follows the same quality bar and produces consistent, actionable feedback, regardless of which engineer assigned the task or which runtime executed it.

---

## When to use this skill

Use this skill whenever an issue is about reviewing, auditing, or providing feedback on code. Trigger phrases that match this skill:

- "Review this function / module / PR"
- "Check this code for issues"
- "Audit this implementation"
- "Does this look right?"
- "Is this production ready?"

Do NOT use this skill for: writing new features, debugging failing tests, or generating documentation. Those have separate skills.

---

## Context: Venti's engineering standards

Venti Technologies builds autonomous vehicle software for logistics fleets. Code in this codebase may directly affect vehicle behavior and fleet safety. Hold the following non-negotiables in every review:

1. **No silent failures.** Every function that processes external input (sensor data, API responses, database reads) must handle missing or malformed data explicitly. Silently returning `None` or an empty result without logging is not acceptable.
2. **Type safety.** All public function signatures must include type hints. Return types must be explicit.
3. **Observability.** Production-critical paths must emit structured log lines (not `print()`). Use Python's `logging` module.
4. **Performance at scale.** Telemetry pipelines process 10,000+ records per second across multiple vehicles. Flag O(n²) operations, unnecessary list copies, or repeated dict lookups inside hot loops.
5. **Security.** Flag hardcoded credentials, unvalidated external inputs used in queries or shell commands, and unencrypted sensitive data.

---

## Review process

When assigned a code review issue, follow this sequence exactly:

### Step 1: Understand the context
Read the issue description and any attached files. Identify:
- What this code does (one sentence)
- Which team owns it (data pipeline, integration, simulation, full-stack)
- Whether it is on a hot path (real-time telemetry, vehicle control) or a background job

### Step 2: Classify by risk level
Assign one of three risk levels before reviewing:

| Level | Criteria |
|-------|----------|
| **Critical** | Code runs in real time on vehicles or affects safety systems |
| **High** | Data pipeline code, fleet management logic, or API-facing endpoints |
| **Standard** | Internal tooling, scripts, tests, dashboards |

State the risk level explicitly at the top of your review comment.

### Step 3: Review the code
Check in this order:

1. **Correctness**: Does the logic match the stated intent? Are there off-by-one errors, incorrect conditionals, or unhandled edge cases?
2. **Error handling**: What happens when keys are missing? When a downstream service is unavailable? When types are wrong?
3. **Type hints**: Are all function signatures annotated? Are complex types (dicts, lists of dicts) typed with `TypedDict` or `dataclass` where appropriate?
4. **Performance**: Is there a more efficient data structure or algorithm? Any unnecessary allocations inside loops?
5. **Observability**: Are key operations logged? Are errors logged with enough context to debug in production?
6. **Security**: See non-negotiables above.
7. **Tests**: Does the issue mention tests? If tests exist, are the cases adequate? If no tests exist, note it.

### Step 4: Write the review comment
Structure your review comment like this:

```
**Risk level:** [Critical / High / Standard]

**Summary:** [One sentence on overall quality and what the biggest issue is]

**Issues found:**

[MUST FIX] Description of the issue, why it matters, and the specific line or
           pattern to change. Include a corrected code snippet where helpful.

[SHOULD FIX] Description of a significant but non-blocking issue.

[CONSIDER] Lower-priority suggestions.

**What's good:** [Acknowledge anything done well, be specific, not generic]
```

Use exactly these labels: `[MUST FIX]`, `[SHOULD FIX]`, `[CONSIDER]`. No other labels.

Do not use generic phrases like "looks good overall" or "nice work" without specifics. Every positive comment must name what is actually good and why.

### Step 5: Change the issue status
After posting the review comment:
- If there are `[MUST FIX]` items: set status to **In Review** and assign back to the original author.
- If there are only `[SHOULD FIX]` or `[CONSIDER]` items: set status to **In Review** with a comment that it can be merged after addressing the suggestions.
- If no issues found: set status to **Done**.

---

## Example output

```
**Risk level:** High

**Summary:** The telemetry parser does not handle missing fields and will raise
KeyError in production when a sensor drops a field. Needs error handling before merge.

**Issues found:**

[MUST FIX] `record['speed']` on line 4 raises `KeyError` if the speed field is
absent (happens during GPS blackout events). Use `record.get('speed')` with a
sentinel value, or validate the schema at ingestion time with a TypedDict.

[MUST FIX] No logging. If this function raises, nothing in the logs will show
which record caused the failure. Wrap the loop body in try/except and log
`sensor_id` and `timestamp` on failure.

[SHOULD FIX] The return type is unannotated. Add `-> list[TelemetryRecord]`
and define `TelemetryRecord` as a TypedDict.

[CONSIDER] At 10k records/sec, appending to a list then returning is fine,
but if this grows, consider a generator to avoid materializing the full batch.

**What's good:** The field naming in the output dict is consistent with the
downstream schema spec, which will save debugging time later.
```

---

## Notes

- Always post the review as a comment on the issue, not as a standalone message.
- If the code is too long to review in one pass, split it into sections and post separate comments per section, clearly labelled "Part 1 of N".
- If you find a security issue of any severity, always mark it `[MUST FIX]` regardless of the overall risk level.

---

## CHANGELOG

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | May 2026 | Initial version. Five non-negotiables, three risk levels, structured output format. |
