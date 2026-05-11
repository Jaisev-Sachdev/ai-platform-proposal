# Venti AI Platform

Unified AI coding platform for Venti Technologies engineering teams.

**Multica** for agent and task management. **Arize Phoenix** for LLM observability. Both self-hosted. All data on your infrastructure.

Read [`PROPOSAL.md`](./PROPOSAL.md) for the full architecture and rollout plan.

---

## What this repository contains

| File / Directory | Purpose |
|-----------------|---------|
| `docker-compose.phoenix.yml` | Runs Phoenix + its PostgreSQL database |
| `.env.example` | Environment variable reference: copy to `.env` |
| `Makefile` | Shortcuts for every operation (`make help` to list all) |
| `demo/demo.py` | Tracing demo: 3 Claude API calls, all captured in Phoenix |
| `demo/requirements.txt` | Python dependencies for the demo |
| `skills/venti-code-review/SKILL.md` | Shared code review skill for all Multica agents |
| `skills/venti-telemetry-analysis/SKILL.md` | Telemetry domain context skill for data pipeline agents |
| `PROPOSAL.md` | Full written proposal: monitoring strategy, management plan, rollout |

---

## Prerequisites

Install all of these before starting.

| Tool | Version | Install |
|------|---------|---------|
| Docker Desktop | Latest | https://docs.docker.com/get-started/get-docker/ |
| Git | Any | https://git-scm.com/downloads |
| Python | 3.11+ | https://www.python.org/downloads/ |
| Node.js | 18+ | https://nodejs.org/ (required by Multica CLI) |
| Claude Code | Latest | `npm install -g @anthropic-ai/claude-code` |
| Anthropic API key | | https://console.anthropic.com/ |

**Windows users:** Docker Desktop must have WSL2 integration enabled. Install an Ubuntu distro from the Microsoft Store, enable WSL2 in Docker Desktop settings, and run all commands from the Ubuntu WSL2 terminal. Claude Code and the Multica daemon must be installed inside WSL2, not in the Windows host.

---

## Setup (~25 minutes, one-time)

### Step 1: Clone this repository

```bash
git clone https://github.com/Jaisev-Sachdev/ai-platform-proposal.git
cd ai-platform-proposal
```

### Step 2: Create your .env file

```bash
cp .env.example .env
```

Open `.env` and fill in your `ANTHROPIC_API_KEY`. Change `PHOENIX_SECRET` to a random string:

```bash
openssl rand -hex 32   # paste the output into PHOENIX_SECRET in .env
```

### Step 3: Start Phoenix

```bash
make phoenix-up
```

Phoenix will pull its Docker image (first run: ~2 minutes) and start. When ready:

- **Phoenix UI:** http://localhost:6006
- **OTLP gRPC collector:** http://localhost:4317 (your instrumented code sends traces here)

### Step 4: Set up Multica self-hosted server

```bash
make multica-clone    # clones https://github.com/multica-ai/multica into ./multica-server
make multica-up       # runs: cd multica-server && make selfhost
```

When ready:

- **Multica frontend:** http://localhost:3000
- **Multica backend:** http://localhost:8080

Open http://localhost:3000, enter your email, and get the verification code from the server logs:

```bash
make multica-logs     # look for: [DEV] Verification code: XXXXXX
```

Log in and create your first workspace.

### Step 5: Configure the Multica CLI and start the daemon

```bash
make multica-cli-setup
```

This runs `multica setup self-host`, which:
1. Opens a browser to log you in
2. Stores your personal access token locally
3. Auto-detects Claude Code on your PATH and registers it as a runtime
4. Starts the daemon in the background

Verify:

```bash
multica daemon status     # should show: running
multica runtime list      # should show your machine with Claude Code
```

### Step 6: Create your first agent

In the Multica UI (http://localhost:3000):

1. Go to **Agents → + New**
2. Name: `venti-reviewer`
3. AI coding tool: **Claude Code**
4. System instructions:

```
You are a senior software engineer at Venti Technologies, an autonomous vehicle company.
When assigned a code review issue, follow the venti-code-review skill exactly.
Be specific, actionable, and honest. Do not approve code with critical safety issues.
```

5. Visibility: **Workspace**
6. Click **Create**

### Step 7: Import and attach the skills

In the Multica UI:

1. Go to **Agents → Skills → + Import skill → From GitHub**
2. Paste: `https://github.com/Jaisev-Sachdev/ai-platform-proposal/tree/main/skills/venti-code-review`
3. Repeat for: `https://github.com/Jaisev-Sachdev/ai-platform-proposal/tree/main/skills/venti-telemetry-analysis`
4. Go to **Agents → venti-reviewer → Skills → Attach** and attach `venti-code-review`

### Step 8: Assign your first task

In the Multica UI:

1. Go to **Issues → + New issue**
2. Title: `Review: telemetry batch parser`
3. Description: paste in a code snippet or link to a file
4. Assignee: **venti-reviewer**
5. Click **Create**

Watch the agent claim the task within 3 seconds, start working, and post a review comment.

### Step 9: Run the Phoenix demo

```bash
make demo
```

This runs `demo/demo.py`, which makes 3 Claude API calls and sends all traces to Phoenix. After it finishes, open http://localhost:6006 and navigate to **Traces** to see:

- Full prompt and response for each call
- Token usage (input / output / cache)
- Latency per span
- Estimated cost

---

## Daily operations

```bash
make status          # check which containers are running
make phoenix-logs    # follow Phoenix logs
make multica-logs    # follow Multica backend logs
make phoenix-down    # stop Phoenix
make multica-down    # stop Multica
make up              # start everything
make down            # stop everything
```

---

## Adding a new engineer

Each engineer who joins the workspace follows Steps 5–6 only (Steps 1–4 run the shared server, done once).

1. Install prerequisites (Docker, Node.js, Claude Code).
2. Install Multica CLI: `npm install -g @multica/cli`
3. Configure CLI: `multica setup self-host --server-url http://<server-address>:8080 --app-url http://<server-address>:3000`
4. Start daemon: `multica daemon start`
5. Accept workspace invite from the team lead in Multica UI.

---

## Adding a new skill

1. Create a new directory under `skills/` in this repository.
2. Write a `SKILL.md` following the structure of the existing skills.
3. Open a pull request. The team lead reviews and merges.
4. Import the skill into Multica from GitHub (Agents → Skills → Import → From GitHub).
5. Attach to the appropriate agent(s).

---

## Troubleshooting

**Multica daemon shows offline**

```bash
multica daemon status    # check if running
multica daemon logs -f   # look for errors
multica daemon restart   # restart
```

In the Multica UI, go to Runtimes. Your runtime should show "online" within 15 seconds of the daemon starting.

**Phoenix not receiving traces**

Make sure Phoenix is running: `make phoenix-status`. Make sure your `PHOENIX_COLLECTOR_ENDPOINT` in `.env` is `http://localhost:4317`. Try running the demo: `make demo`. If traces still don't appear, check Phoenix logs: `make phoenix-logs`.

**Multica verification code not received by email**

Email is not configured for local development. The code is printed to the server logs. Run `make multica-logs` and look for `[DEV] Verification code: XXXXXX`.

**`make multica-up` fails on first run**

This usually means the Multica Docker images haven't been published yet for the version tag. Try:

```bash
cd multica-server && make selfhost-build
```

This builds from source instead of pulling pre-built images.

**Port conflicts**

| Default port | Used by | Change via |
|-------------|---------|------------|
| 3000 | Multica frontend | Multica's docker-compose.selfhost.yml |
| 8080 | Multica backend | Multica's docker-compose.selfhost.yml |
| 5432 | Multica PostgreSQL | Multica's docker-compose.selfhost.yml |
| 6006 | Phoenix UI | `docker-compose.phoenix.yml` |
| 4317 | Phoenix OTLP gRPC | `docker-compose.phoenix.yml` |
| 4318 | Phoenix OTLP HTTP | `docker-compose.phoenix.yml` |
| 5433 | Phoenix PostgreSQL | `docker-compose.phoenix.yml` (external only) |

---

## References

- [Multica documentation](https://multica.ai/docs)
- [Multica GitHub](https://github.com/multica-ai/multica)
- [Arize Phoenix documentation](https://arize.com/docs/phoenix)
- [Arize Phoenix GitHub](https://github.com/Arize-ai/phoenix)
- [OpenInference instrumentation](https://github.com/Arize-ai/openinference)
- [Full proposal](./PROPOSAL.md)
