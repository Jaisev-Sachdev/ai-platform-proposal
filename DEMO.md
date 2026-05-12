# Live Demo Walkthrough

A full walkthrough of the Venti AI Platform demo is documented in `venti-demo.docx` (available on request) and the accompanying screen recording.

## What the demo covers

1. Multica self-hosted server running locally with the Venti Technologies workspace
2. JAISEVS-PC registered as a runtime with Claude Code, status Online
3. venti-reviewer agent created with Venti-specific review standards and Workspace visibility
4. Both skills imported directly from this GitHub repo (venti-code-review, venti-telemetry-analysis)
5. Issue created: "Review: vehicle telemetry batch processor for production readiness"
6. Agent autonomously claims the task, analyses the code with AV domain context, posts a structured review
7. Review classified Critical risk, three [MUST FIX] items with concrete code fixes, one [SHOULD FIX], one [CONSIDER]
8. Phoenix capturing all AI calls as traces with full prompt, response, token count, latency, and cost

## Agent review output (excerpt)

**Risk level:** Critical

**Summary:** This function will crash the entire batch on any missing field, including GPS during the tunnel blackouts described in the context, and provides zero observability into what was dropped or why.

**[MUST FIX]** KeyError on all four telemetry fields — use `.get()` with explicit handling for required vs optional fields.

**[MUST FIX]** No type hints on public functio
# Add DEMO.md
cat > ~/ai-platform-proposal/DEMO.md << 'EOF'
# Live Demo Walkthrough

A full walkthrough of the Venti AI Platform demo is documented in `venti-demo.docx` (available on request) and the accompanying screen recording.

## What the demo covers

1. Multica self-hosted server running locally with the Venti Technologies workspace
2. JAISEVS-PC registered as a runtime with Claude Code, status Online
3. venti-reviewer agent created with Venti-specific review standards and Workspace visibility
4. Both skills imported directly from this GitHub repo (venti-code-review, venti-telemetry-analysis)
5. Issue created: "Review: vehicle telemetry batch processor for production readiness"
6. Agent autonomously claims the task, analyses the code with AV domain context, posts a structured review
7. Review classified Critical risk, three [MUST FIX] items with concrete code fixes, one [SHOULD FIX], one [CONSIDER]
8. Phoenix capturing all AI calls as traces with full prompt, response, token count, latency, and cost

## Agent review output (excerpt)

**Risk level:** Critical

**Summary:** This function will crash the entire batch on any missing field, including GPS during the tunnel blackouts described in the context, and provides zero observability into what was dropped or why.

**[MUST FIX]** KeyError on all four telemetry fields — use `.get()` with explicit handling for required vs optional fields.

**[MUST FIX]** No type hints on public function signature.

**[MUST FIX]** No structured logging — silent failures in a production-critical path.

**[SHOULD FIX]** No guard on `batch` itself.

**[CONSIDER]** Shallow copy of nested GPS dict.

## Stack

| Component | Purpose | URL |
|-----------|---------|-----|
| Multica (self-hosted) | Agent orchestration, kanban board | http://localhost:3000 |
| Arize Phoenix | LLM observability, trace dashboard | http://localhost:6006 |
| LiteLLM Proxy | Bridges Claude Code to Phoenix | http://localhost:4000 |
