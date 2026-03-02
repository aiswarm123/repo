# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **aiswarm** project — an AI agent orchestration setup. The repository is managed by an external `agent-orchestrator` tool (configured via `agent-orchestrator.yaml`) that spins up Claude Code agents in git worktrees inside tmux sessions.

## Architecture

### agent-orchestrator.yaml
Top-level configuration consumed by the `agent-orchestrator` tool:
- `dataDir: ~/.agent-orchestrator` — where the orchestrator stores its own state
- `worktreeDir: ~/.worktrees` — where git worktrees for agent sessions are created
- `port: 3001` — orchestrator API/UI port
- Defaults: runtime `tmux`, agent `claude-code`, workspace `worktree`, notifier `desktop`
- Project entry `aiswarm` maps to this repo path and its upstream GitHub repo

### .claude/settings.json — PostToolUse Hook
After every `Bash` tool call, `.claude/metadata-updater.sh` is invoked automatically. This hook keeps the orchestrator's session metadata in sync with agent actions.

### .claude/metadata-updater.sh — Session Metadata Updater
Reads JSON from stdin (the hook payload) and writes key=value pairs to the session metadata file at `$AO_DATA_DIR/$AO_SESSION`.

Tracked events:
| Command pattern | Metadata updated |
|---|---|
| `gh pr create` | `pr=<url>`, `status=pr_open` |
| `git checkout -b <branch>` / `git switch -c <branch>` | `branch=<name>` |
| `git checkout <feature-branch>` / `git switch <feature-branch>` | `branch=<name>` |
| `gh pr merge` | `status=merged` |

**Required environment variables at runtime:**
- `AO_SESSION` — session identifier (filename under `AO_DATA_DIR`)
- `AO_DATA_DIR` — path to the sessions directory (default: `~/.ao-sessions`)

These are injected by the `agent-orchestrator` tool when it launches an agent session.
