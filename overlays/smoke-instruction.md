Runtime tooling check: if a coding MCP is available, use it for initial repository
exploration before falling back to shell search. Its initial graph has already been
built for /app. Use returned source evidence to guide your work; do not assume an
index remains current after edits. If no MCP is configured, use grep/ripgrep for
initial exploration. Report connection errors or unusable results rather than
silently claiming the tool worked. Solve and check the task normally.
