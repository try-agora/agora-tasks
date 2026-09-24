# Choose the tool independently

Tasks define the work and the scoring. Harbor chooses the agent and its tools at launch.
No task imports a knowledge product, installs one, requires its command names, or reads
its private database to award a score.

## No-tool baseline

Run a task with your chosen Harbor agent and model. Do not inject a memory skill or MCP
configuration. The model, budget, task revision, and network policy must match other arms.

## Plain-notes control

Append the same generic notes instruction to every task or step:

```sh
uv run harbor run -p evals/cross-session-framework-reuse \
  -a claude-code -m "$MODEL" --env docker --jobs-dir evals/jobs \
  --allow-agent-host api.anthropic.com \
  --extra-instruction-path tools/notes.md
```

The control uses native file operations, with no additional dependency.
The fresh conversation can read /memory/NOTES.md after the source workspace resets.
This is a control condition, not a claim that a memory product is integrated.

## Your knowledge tool

Use Harbor's native `--mcp-config /path/to/tool.mcp.json` to inject an MCP tool,
or `--skill /path/to/vendor-skill` for an installed tool's native instructions.
These are run settings; never modify the task instruction or verifier for one arm.
For CLI tools needing binaries, package installation belongs in a separately versioned
agent/environment integration. A skill alone does not install the tool.

Keep tool state outside /app (for example, /memory), namespace external state per trial,
and start it empty. External services need their own isolated deployment and explicit
network allowlist. Pass secrets at runtime, never in task source or Docker images.
Pin and record the tool version, configuration, adoption instructions, and state-reset
procedure with the job. No vendor integration is claimed as tested by this release.

Harbor references:
[MCP configuration](https://docs.harborframework.com/core-concepts/jobs/configs),
[skills](https://docs.harborframework.com/core-concepts/jobs/skills).
