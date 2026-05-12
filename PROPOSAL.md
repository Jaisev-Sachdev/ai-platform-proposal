# Unified AI Coding Platform: Proposal for Venti Technologies

**Prepared by:** Jaisev Sachdev
**Date:** May 2026
**Version:** 1.0
**Status:** Draft for review, Wang Qiang (Principal Software Engineer)

---

## Executive Summary

The core problem this proposal addresses is not that Venti engineers use AI badly. It is that every engineer uses it differently. Two engineers asking Claude to review the same piece of code will get two different responses, in two different formats, catching two different sets of issues, because each has learned to prompt in their own way. There is no shared standard, no shared knowledge base, and no way to measure whether AI-assisted work is getting better or worse over time. As the team grows and AI usage increases, this inconsistency compounds.

This proposal recommends adopting two open-source tools in tandem: **Multica** for unified agent and task management, and **Arize Phoenix** for LLM observability, with **LiteLLM** as the proxy layer that connects them. Together they solve the consistency problem at its root: instead of each engineer prompting Claude independently, the whole team shares a common agent with shared instructions, shared domain context, and a shared output format. Every code review follows the same standard. Every data pipeline task uses the same domain knowledge. Every AI call is visible, auditable, and attributable.

This has been demonstrated concretely. A benchmark experiment run as part of this proposal compared generic ad-hoc prompting against the standardised venti-reviewer agent across four representative Venti code samples. The structure score was 0.00 for ad-hoc prompting versus 1.00 for the standardised agent. The format, risk classification, and label structure were consistent on every single run from the agent, and inconsistent on every single run without it. That is the unification argument measured.

Both tools are fully self-hostable. All code, prompts, and trace data remain on Venti's infrastructure at all times.

---

## 1. Problem Statement

### 1.1 The Current State

Each engineer at Venti independently configures and uses AI coding assistants. The practical result:

- **Inconsistent output.** Two engineers asking the same question get different results based on how each has learned to prompt. There is no shared standard, no shared system instructions, and no shared configuration. A code review from one agent does not follow the same checklist as a review from another.
- **Non-reproducible workflows.** When an engineer finds an effective way to use Claude Code for a task, that knowledge stays on their machine. It is not captured, versioned, or shared.
- **No visibility.** Questions like "how many tokens are we using per week?", "which projects are consuming the most AI resources?", and "what is our cost per engineer?" cannot be answered. Each engineer's usage is siloed with no aggregated view across the team.

Without intervention these problems compound. The solution is not to restrict how engineers use AI. It is to provide a shared management and observability layer that makes AI usage consistent, measurable, and improvable.

---

## 2. Proposed Solution

### 2.1 Architecture Overview

The proposed stack has two layers:

```
┌─────────────────────────────────────────────────────────────────┐
│                        MULTICA (self-hosted)                    │
│   Project management layer for human + agent teams              │
│                                                                 │
│   Workspaces · Issues · Projects · Comments                     │
│   Agents · Skills library · Runtimes dashboard                  │
│                                                                 │
│   Server: Docker (internal VM or shared dev machine)            │
│   Frontend: http://multica.internal:3000                        │
└────────────────────────┬────────────────────────────────────────┘
                         │ assigns tasks / streams progress
             ┌───────────▼────────────┐
             │   multica daemon       │  ← runs on each engineer's
             │   (local, per machine) │    machine, drives AI tools
             └───────────┬────────────┘
                         │ invokes
             ┌───────────▼────────────┐
             │   Claude Code          │  ← or Codex, Gemini, etc.
             │   (local CLI)          │    API keys stay local
             └───────────┬────────────┘
                         │ all API calls route through proxy
             ┌───────────▼────────────┐
             │   LiteLLM Proxy        │  ← localhost:4000
             │   (local, per machine) │    intercepts every call
             └──────┬─────────┬───────┘
                    │         │ traces every call via OTLP
                    │         ▼
                    │  ┌──────────────────────────────────────────┐
                    │  │        ARIZE PHOENIX (self-hosted)        │
                    │  │   LLM observability layer                 │
                    │  │                                           │
                    │  │   Traces · Evaluations · Datasets         │
                    │  │   Prompt experiments                      │
                    │  │                                           │
                    │  │   UI: http://phoenix.internal:6006        │
                    │  │   OTLP: http://phoenix.internal:4317      │
                    │  └──────────────────────────────────────────┘
                    │ forwards request
                    ▼
             Anthropic API
```

**Multica** is the team's issue tracker and workflow surface. It has a kanban board with seven statuses (Backlog, Todo, In Progress, In Review, Done, Blocked, Cancelled), Jira-style issue numbers (`PREFIX-123`), projects, comments, and priority levels, the same shape as Linear or Jira. The defining difference is that the assignee on any issue can be a person or an agent. An engineer assigns a ticket to `venti-reviewer` the same way they would assign it to a colleague; the agent claims it within seconds, works, posts comments, and moves the ticket to Done. The whole team sees this on the same kanban they use for their own work. Nothing about the workflow changes; agents just become teammates on the board.

**Phoenix** is the observability layer. It is the answer to "how do we see what the AI is actually doing, how much it costs, and whether it is getting better or worse?" Every Anthropic SDK call made by any Claude Code agent flows through Phoenix as an OpenTelemetry trace span.

**How this solves the consistency problem.** Today, every engineer's AI setup is their own island: different prompts, different instructions, different habits, no shared knowledge. Multica collapses that by making agents (with their standardised system instructions and shared skills) the team's common interface to AI. When an engineer assigns a code review ticket to `venti-reviewer`, they get the same output whether they are a junior engineer on their first week or a senior who has been at Venti for three years, because the agent's behaviour is defined by shared skills and instructions that the whole team owns and iterates on. The kanban board makes AI-assisted work visible and trackable alongside human work, so it is managed rather than ad hoc. Phoenix adds the measurement layer: every AI call is traced, so the team can see whether the standardised approach is actually producing better output over time, and adjust the skills when it is not. Consistency is not enforced by restricting engineers; it is achieved by giving agents a shared, versioned definition of how to do each type of task.

The two tools are complementary. Multica provides the workflow surface; Phoenix provides the measurement surface. Neither is redundant.

### 2.2 Key Properties

- **No code on Multica's or Arize's servers.** Multica's server only stores task metadata (issue descriptions, comments, agent configs). It never sees API keys or code. Agent execution happens on engineers' local machines via the daemon. Phoenix is self-hosted; all traces stay on Venti's infrastructure.
- **No new AI provider.** The proposal uses Claude Code (Anthropic) as the coding assistant. Multica is the management layer on top, not a replacement for it.
- **Self-hostable, open-source.** Both Multica and Phoenix are open source and run entirely in Docker. No per-seat SaaS fees. No vendor lock-in.
- **Cross-platform.** Docker Compose works identically on macOS and Linux. Windows requires Docker Desktop with WSL2, which is standard for developers on that platform.

---

## 3. Monitoring Strategy

> "The whole system should be measurable and monitored." (Wang Qiang)

Phoenix provides three monitoring surfaces: per-call traces, project-level aggregation, and evaluation scoring.

### 3.1 What Phoenix Captures

Every AI call instrumented through Phoenix captures:

| Signal | What it tells you |
|--------|------------------|
| **Full prompt + response** | Exact inputs and outputs. Audit any call at any time. |
| **Token usage** | Input tokens, output tokens, cache read, cache write; tracked per call and in aggregate. |
| **Latency** | Wall-clock time per span. Identify which tasks are slow. |
| **Cost** | Estimated cost per call, per project, per time window. |
| **Tool calls** | When Claude Code invokes tools (file reads, bash commands, etc.), each tool call is a child span. |
| **Error rate** | Which calls failed, with the full error context. |
| **Model** | Which model version was used, so you can compare Sonnet vs. Opus. |

### 3.2 Monitoring by Dimension

**Per engineer:** Each engineer's daemon connects to a named project in Phoenix. The Runtimes dashboard in Multica shows online/offline status, usage charts, and activity heatmaps per runtime. In Phoenix, filter by project or runtime to see one engineer's usage.

**Per team / department:** Create one Multica workspace per team. Each workspace's agents emit traces tagged with the workspace name. Phoenix filters by project name, giving per-team cost and activity dashboards.

**Per issue / task:** Every task executed through Multica has a unique task ID (format: `PREFIX-123`). To link a Phoenix trace to a specific Multica issue, set the task ID as a span attribute on a parent span that wraps all API calls for that task. In a Multica agent context, the task ID is available as the environment variable `MULTICA_TASK_ID` injected by the daemon at runtime. The demo script (`demo/demo.py`) shows a working implementation: a root span is opened with `tracer.start_as_current_span(f"agent-task:{MULTICA_TASK_ID}")`, Multica metadata is attached via `root_span.set_attribute("multica.task_id", ...)`, and all API calls made within that context become child spans under the same trace. This produces a single trace in Phoenix per Multica task, with all AI calls grouped and attributable to the issue that triggered them.

**Over time:** Phoenix stores all traces in PostgreSQL. You can query historical data, export to CSV, or build dashboards over weekly/monthly windows.

### 3.3 Evaluation (Quality Scoring)

Raw traces tell you what happened. Evaluations tell you whether it was any good.

Phoenix ships with built-in LLM-as-judge evaluators for:
- **Relevance:** Did the response actually address the prompt?
- **Hallucination:** Did the response make claims unsupported by context?
- **Q&A correctness:** For tasks with a verifiable right answer.
- **Code quality:** Custom evaluator (see below).

The evaluation pipeline reads completed traces and scores each response. Scores are attached to the trace and visible in the dashboard. Over time, you can track whether agent output quality is improving, staying flat, or regressing. This feedback loop is what makes the skills library valuable over time.

### 3.4 Code Review and Style Conformance Scoring

Beyond general LLM evaluations, two domain-specific scoring systems are proposed for Venti's engineering context.

#### Code review quality score

Each completed code review trace receives three LLM-as-judge scores:

| Dimension | Question | Range |
|-----------|----------|-------|
| **Relevance** | Did the review address the actual code shown? | 0.0 to 1.0 |
| **Specificity** | Does the review include concrete line-level feedback? | 0.0 to 1.0 |
| **Actionability** | Does each issue include a suggested fix? | 0.0 to 1.0 |

A composite score is stored as a custom Phoenix span attribute, enabling quality trend tracking and early detection of skill regressions.

#### Code style conformance score

When `venti-reviewer` processes a Python file, it checks against Venti's style standards using `black`, `flake8`, and `mypy`:

| Attribute | What it captures |
|-----------|-----------------|
| `lint.format_errors` | Formatting violations (black) |
| `lint.style_errors` | Style violations (flake8) |
| `lint.type_errors` | Type annotation errors (mypy) |
| `lint.conformance_score` | 1 minus (total errors / lines of code), 0.0–1.0 |

Trend lines in Phoenix show whether AI-generated code is getting cleaner or drifting from team standards over time.

### 3.5 Alerting (Phase 2)

Phoenix's data is stored in PostgreSQL and accessible via a GraphQL API. In Phase 2, implement:

- Daily cost report sent to the team lead via webhook or email: "Yesterday's AI usage: X tokens, estimated $Y."
- Alert if any single task exceeds a cost threshold (e.g. $2 per task, to prevent runaway loops).
- Alert if error rate on a specific agent exceeds a threshold (daemon is crashing, key expired, etc.).

---

## 4. Management Strategy

### 4.1 Runtimes

A runtime in Multica is the pairing of one daemon instance on one machine with one AI coding tool. One machine with Claude Code installed contributes one runtime per workspace it belongs to.

**Provisioning:** Each engineer installs the Multica CLI, runs `multica setup self-host` (pointing at the internal server URL), and starts the daemon with `multica daemon start`. This takes approximately 10 minutes. The daemon auto-detects Claude Code on startup and registers the runtime.

**Monitoring:** The Runtimes page in the Multica UI shows each runtime's online/offline status, heartbeat recency, and activity heatmap. Runtimes send heartbeats every 15 seconds; a runtime is marked offline after 45 seconds without a heartbeat. Offline runtimes are surfaced prominently in the dashboard, so the team lead can see at a glance if any machine is down.

**Future:** Multica has announced cloud runtimes (currently waitlist-only). Once available, agents can run without a local daemon, enabling batch jobs that run when engineers are offline. Worth evaluating when it becomes available.

### 4.2 Agents

An agent in Multica is a named, configured worker with a specific role, system instructions, attached skills, and a concurrency limit. Agents appear in the same assignee dropdown as humans.

#### Agent taxonomy for Venti

Recommend creating four agent types, each with a specific role and set of attached skills:

| Agent name | Role | Skills attached | Concurrency |
|------------|------|-----------------|-------------|
| `venti-reviewer` | Code review on any Venti PR or issue | `venti-code-review` | 3 |
| `venti-telemetry-dev` | Write / improve telemetry pipeline code | `venti-telemetry-analysis`, `venti-code-review` | 2 |
| `venti-test-writer` | Generate unit and integration test files | `venti-code-review` | 4 |
| `venti-docs` | Write inline docstrings and README sections | (none initially) | 6 |

Each agent should have explicit `system_instructions` defining its role, the codebase conventions it should follow, and what it must never do (e.g. "Do not modify test files when assigned a production code task").

**Naming convention:** Use `venti-{role}` for workspace-wide agents. Private agents owned by individual engineers can use `{initials}-{role}` (e.g. `js-telemetry-dev`).

**Visibility:** Workspace-wide agents should have visibility set to `workspace` so any team member can assign them. Private experimental agents default to `private`.

**Lifecycle:** Archive agents that are no longer used. Their task history is preserved. Archived agents can be restored. Do not delete agents; deletion removes history.

**Security note:** The `custom_env` field (used to inject `ANTHROPIC_API_KEY` and similar) stores values in plaintext in Multica's database. Use read-only, limited-scope keys for agents. Rotate these keys on a schedule, especially if an agent's config is ever shared outside the team. Do not store database passwords or root tokens in `custom_env`.

### 4.3 Skills

A skill is a `SKILL.md` file (plus optional supporting scripts or templates) that tells the agent how to approach a specific type of task. Skills are the mechanism by which institutional knowledge is captured, versioned, and shared team-wide.

This repository includes two production-ready starter skills:

- **`venti-code-review`**: standardises code reviews with Venti-specific standards (field handling, type hints, observability, AV safety context). Produces consistent review comments with `[MUST FIX]` / `[SHOULD FIX]` / `[CONSIDER]` labels.
- **`venti-telemetry-analysis`**: gives the agent domain context for telemetry pipeline work: record schema, known failure modes (field dropout, GPS quality degradation, duplicate delivery), performance expectations, and output standards.

#### Skill governance

**Authoring:** Skills are written in Markdown and stored in this repository under `skills/`. Any engineer can propose a new skill via a pull request. The PR is reviewed by the team lead before import into the Multica workspace.

**Import:** Once approved, import the skill from GitHub into the Multica workspace: Agents → Skills → Import from GitHub → paste the directory URL. Skills become available to attach to any agent immediately.

**Versioning:** Bump the version in the skill's `SKILL.md` header on every change. Multica does not currently version skills automatically; the version field in the skill file is the source of truth. Keep a `CHANGELOG` section at the bottom of each `SKILL.md`.

**Security:** Do not import third-party skills from GitHub without reviewing every file first. Malicious instructions have been planted in publicly available skill packs and can exfiltrate API keys or execute arbitrary commands on the engineer's machine. Automated scanning is not a substitute for human review. For skills involving sensitive data, prefer skills written in-house.

**Growth path:** The expected trajectory is one new skill per sprint, authored by whoever solves a repeatable problem first. By month six, the library should cover the most common task types for each team. This is the compounding return on investment: the team's AI capability grows with every skill added, and it grows for everyone simultaneously.

---

## 5. Department-Specific Use Cases

### 5.1 Full-Stack Engineering

Primary workflows: building and maintaining the fleet management web application, API development, database schema changes.

| Task | Agent | Skill |
|------|-------|-------|
| API endpoint code review | `venti-reviewer` | `venti-code-review` |
| Database migration script generation | `venti-telemetry-dev` | (to be authored: `venti-db-migrations`) |
| Frontend component generation | `venti-docs` | (to be authored: `venti-frontend`) |
| Docstring and README writing | `venti-docs` | (none) |

Phoenix will capture all AI calls for this team under project `venti-fullstack`, enabling cost attribution separate from other departments.

### 5.2 Integration and Validation (IV)

Primary workflows: validating AV software builds against real vehicle hardware, integration test suites, debugging hardware failures.

| Task | Agent | Skill |
|------|-------|-------|
| Integration test generation | `venti-test-writer` | `venti-code-review` |
| Failure log analysis | `venti-reviewer` | (to be authored: `venti-log-analysis`) |
| Validation script review | `venti-reviewer` | `venti-code-review` |

### 5.3 Simulation Engineering

Primary workflows: virtual test environments, scenario scripts, simulator fidelity validation.

| Task | Agent | Skill |
|------|-------|-------|
| Scenario script generation | `venti-telemetry-dev` | (to be authored: `venti-simulation`) |
| Test harness code review | `venti-reviewer` | `venti-code-review` |
| Performance profiling | `venti-reviewer` | `venti-code-review` |

### 5.4 Data Software and Services (Wang Qiang's team)

Primary workflows: vehicle telemetry ingestion, fleet analytics, data pipeline tooling.

| Task | Agent | Skill |
|------|-------|-------|
| Telemetry parser writing | `venti-telemetry-dev` | `venti-telemetry-analysis` |
| Pipeline code review | `venti-reviewer` | `venti-code-review`, `venti-telemetry-analysis` |
| Query optimisation | `venti-telemetry-dev` | `venti-telemetry-analysis` |
| Data quality analysis | `venti-telemetry-dev` | `venti-telemetry-analysis` |

---

## 6. Rollout Plan

### Phase 1: Pilot (Week 1–2)

**Scope:** Data Software & Services team only (Wang Qiang's team, ~5 engineers).

**Deliverables:**
- Self-hosted Multica server running on a shared internal machine or dev VM.
- Phoenix running alongside it.
- All engineers have the daemon installed and running.
- Two agents created: `venti-reviewer` and `venti-telemetry-dev`.
- Both skills imported and attached to the appropriate agents.
- First tasks assigned and completed.
- Demo walkthrough for the team: how to assign an issue, how to @-mention an agent, how to read a trace in Phoenix.

**Success criteria:**
- Every engineer has at least one completed agent-assigned task.
- Phoenix dashboard shows traces from all team members.
- Team lead can see per-engineer usage from the Multica Runtimes dashboard.

### Phase 2: Expand (Week 3–4)

**Scope:** Add Integration & Validation team.

**Deliverables:**
- IV team onboarded (daemon install, workspace invite).
- `venti-test-writer` agent created with appropriate system instructions.
- `venti-log-analysis` skill authored (by the IV team lead or Jaisev, based on IV team's common patterns).
- Phoenix projects created per team for separate cost attribution.
- Weekly cost report set up (simple Python script querying Phoenix's GraphQL API, emailing a summary).

**Success criteria:**
- IV team has at least three agent-completed tasks.
- Cost report running weekly.

### Phase 3: Full Rollout (Week 5–8)

**Scope:** All remaining engineering departments.

**Deliverables:**
- All departments onboarded.
- Department-specific agents and skills created for each team.
- Evaluation pipeline enabled in Phoenix (LLM-as-judge scoring on completed code review tasks).
- Skills library has at least 6 skills covering the most common task types.
- Onboarding documentation written (engineer setup guide, agent assignment walkthrough, skills authoring guide).

**Success criteria:**
- All engineers using the platform.
- Evaluation scores available for agent-completed code reviews.
- Skills library in active use: at least one new skill added per sprint.

### Phase 4: Optimise (Ongoing)

- Monitor evaluation scores and use them to improve skills.
- Introduce Autopilots for standing recurring tasks (e.g. daily standup summaries, weekly code quality reports).
- Evaluate Multica cloud runtimes (currently on waitlist) for batch overnight jobs.
- Use Phoenix's Experiments feature to A/B test prompt changes across the same dataset of tasks.
- Explore whether Phoenix traces can feed back into skills: identify failure patterns in traces, encode fixes as new skill guidance.

---

## 7. Why Self-Hosted

Several alternatives were considered. The recommendation is self-hosted for all components.

**Why not Multica Cloud or Phoenix Cloud?** Both managed options would route Venti's code, issue descriptions, prompts, and responses through third-party servers. For an AV company with proprietary vehicle software, keeping all of this on-premise is non-negotiable. Both tools are a single Docker command to self-host and require minimal maintenance.

**Why not build a custom solution?** Building equivalent task management, agent orchestration, observability, and a skills standard from scratch would take months. Multica and Phoenix are production-grade, actively maintained, and open source. Operating them costs far less than building them.

---

## 8. Security Considerations

| Risk | Mitigation |
|------|------------|
| API keys in agent `custom_env` | Use limited-scope keys per agent. Rotate on a schedule. Never use production root keys. |
| Third-party skill imports | Review every file in any skill imported from external sources before deploying. Malicious instructions have been found in publicly available skill packs. |
| Multica server access | Set `ALLOWED_EMAIL_DOMAINS=ventitech.ai` in `.env` to restrict signup to Venti email addresses only. |
| Phoenix access | Enable `PHOENIX_ENABLE_AUTH=true` for production. Generate a strong `PHOENIX_SECRET` with `openssl rand -hex 32`. |
| Code in agent tasks | Agents execute on engineers' local machines. Agents never have access to production infrastructure unless explicitly granted by the engineer running the daemon. |
| Multica analytics opt-out | Set `ANALYTICS_DISABLED=true` in Multica's `.env` to prevent the server from reporting usage analytics to Multica's PostHog instance. |

---

## 9. Open Questions

The following questions should be addressed before Phase 2:

1. **Relationship to existing issue tracking.** If Venti currently uses Jira or a similar tool, the team needs a clear position on how Multica sits alongside it. Multica does not currently have a Jira sync integration, so running both in parallel means managing two issue trackers. Recommendation: during the Phase 1 pilot, run Multica as a separate workspace specifically for AI-assisted tasks, without attempting to mirror Jira. Evaluate full migration to Multica as the team's primary tracker after the pilot, once the team is comfortable with the workflow.

2. **Infrastructure for the Multica server.** Should it run on an existing internal VM, a dedicated machine, or a cloud VM? Who is responsible for keeping it up? Recommendation: start on a developer's machine for Phase 1, migrate to a dedicated internal VM before Phase 2.

3. **API key management.** Should engineers use their own Anthropic API keys (billed to their accounts), or should Venti provision a company API key? A company key enables consolidated billing and cost attribution but requires careful scoping. A proxy (e.g. LiteLLM) can add per-engineer rate limits and usage attribution on top of a single key. Recommend evaluating this in Phase 2.

4. **Multica cloud runtimes.** Cloud runtimes (currently on waitlist) would allow agent tasks to run without a local daemon. This changes the onboarding story significantly: no local setup required. Sign up for the waitlist and evaluate when available.

5. **Skill review process.** Who reviews skill PRs before import? Recommendation: the team lead (Wang Qiang) for the initial library; delegate to senior engineers as the library matures.

6. **Baseline for scoring.** Section 3.4 defines the scoring rubric (relevance, specificity, actionability for code reviews; black/flake8/mypy for style conformance). Before the evaluation pipeline goes live, the team should run the scorers against a representative sample of existing human-written code reviews to establish a baseline. Without a baseline, scores are absolute numbers with no frame of reference. Collect 20-30 historical review comments and score them to set the "human baseline" before agent scores can be compared meaningfully.

7. **LiteLLM proxy and extended thinking compatibility.** Claude Code's default model (`claude-sonnet-4-6`) sends extended thinking parameters that the current LiteLLM proxy configuration does not fully strip before forwarding to Anthropic. In the Phase 1 pilot, engineers should set `CLAUDE_CODE_DISABLE_EXTENDED_THINKING=1` in their environment when running the daemon to avoid API errors. The longer-term fix is either pinning Claude Code to a model that does not use extended thinking by default, or configuring LiteLLM's `drop_params` handling to correctly intercept this specific parameter. This is a configuration issue, not an architectural one, and does not affect the observability data quality once resolved.

---

## 10. Role of the AI Platform Advocate

This proposal is not a one-time setup. The system compounds in value only if someone actively owns it: onboarding engineers, authoring new skills, maintaining the infrastructure, gathering feedback, and iterating.

As the person proposing this system, I am volunteering to own that role during the internship. Concretely, that means:

- **Onboarding.** Running setup sessions with each engineer joining the platform. Writing and maintaining the onboarding guide. Being the first point of contact when something breaks.
- **Skills authorship.** Writing new skills as the team identifies repeatable task patterns. Each new skill compounds value for the entire team. The goal is at least one new skill per sprint during Phase 1.
- **Platform health.** Monitoring the Multica and Phoenix containers, handling version upgrades, and resolving configuration issues so engineers do not have to.
- **Measurement.** Running the evaluation benchmarks on a regular cadence to track whether agent output quality is improving. Presenting results to the team lead with specific recommendations for skill updates when scores drop.
- **Advocacy.** Running internal demos for new teams before Phase 2 and Phase 3 onboarding. Collecting friction points from early adopters and feeding them back into the skills and configuration.

I will work under Wang Qiang's direction on all of the above. The expectation is not that I operate independently, but that the platform has a dedicated owner who treats it as a product, not infrastructure.

---

## 11. Next Steps

Immediate actions following review of this proposal:

1. **Confirm internal hosting target** for the Multica + Phoenix server.
2. **Schedule a 30-minute setup session** with Wang Qiang to bring up the stack locally, walk through the demo, and verify the Phoenix traces appear correctly.
3. **Import the two starter skills** into the existing Multica workspace (`venti-code-review`, `venti-telemetry-analysis`).
4. **Create the first two agents** (`venti-reviewer`, `venti-telemetry-dev`) and run the first test task.
5. **Set a Phase 1 completion date** and identify the first task the team will assign through Multica in production.

---

## Appendix A: Repository Contents

```
venti-ai-platform/
├── docker-compose.phoenix.yml     Phoenix + PostgreSQL + LiteLLM proxy, one command
├── litellm/
│   └── config.yaml                LiteLLM proxy configuration (model routing + Phoenix callback)
├── .env.example                   All environment variables documented
├── Makefile                       Shortcuts: make up, make demo, make logs
├── demo/
│   ├── demo.py                    Anthropic SDK + Phoenix instrumentation demo
│   └── requirements.txt
├── skills/
│   ├── venti-code-review/
│   │   └── SKILL.md               Code review skill with Venti standards
│   └── venti-telemetry-analysis/
│       └── SKILL.md               Telemetry domain context skill
└── README.md                      Setup guide, cross-platform, <30 minutes
```

## Appendix B: Key URLs (once running)

| Service | URL | Purpose |
|---------|-----|---------|
| Multica UI | http://localhost:3000 | Workspace, issues, agents, skills |
| Multica API | http://localhost:8080 | Backend API (used by CLI and daemon) |
| Phoenix UI | http://localhost:6006 | Trace dashboard, evaluations, experiments |
| Phoenix OTLP (gRPC) | http://localhost:4317 | Ingest endpoint for instrumented code |
| Phoenix OTLP (HTTP) | http://localhost:4318 | Alternative ingest endpoint |

## Appendix C: References

- Multica documentation: https://multica.ai/docs
- Multica GitHub: https://github.com/multica-ai/multica
- Arize Phoenix documentation: https://arize.com/docs/phoenix
- Arize Phoenix GitHub: https://github.com/Arize-ai/phoenix
- OpenInference (instrumentation library): https://github.com/Arize-ai/openinference
