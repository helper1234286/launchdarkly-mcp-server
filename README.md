# LaunchDarkly MCP Server

An MCP (Model Context Protocol) server that lets AI assistants (Claude, Cursor, etc.) manage [LaunchDarkly](https://launchdarkly.com) feature flags via natural language.

## Quick Start

### Prerequisites

- Python 3.10+
- A LaunchDarkly API access token ([create one here](https://app.launchdarkly.com/settings/authorization))

### Install & Run

```bash
# Install from PyPI
pip install launchdarkly-mcp-server

# Set your API key
export LD_API_KEY="your-api-key-here"

# Run the server
launchdarkly-mcp
```

Or use `uvx` (no install needed):

```bash
export LD_API_KEY="your-api-key-here"
uvx launchdarkly-mcp-server
```

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "launchdarkly": {
      "command": "uvx",
      "args": ["launchdarkly-mcp-server"],
      "env": {
        "LD_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Restart Claude Desktop and look for the hammer icon — your LaunchDarkly tools are ready.

## Available Tools

### Phase 1 — Read-only

| Tool | Description |
|------|-------------|
| `list_projects` | List all projects in the account |
| `list_flags` | List feature flags for a project (filterable by env, limit, offset) |
| `get_flag` | Get detailed flag config including targeting rules |
| `get_environments` | List environments for a project |
| `search_audit_log` | Search audit log with LD filter syntax or convenience params |
| `get_flag_status` | Check if a flag is on/off in a specific environment |

### Phase 2 — Write operations

| Tool | Description |
|------|-------------|
| `toggle_flag` | Turn a flag on/off in a specific environment |
| `update_flag_targeting` | Add or remove users/contexts from targeting |
| `create_flag` | Create a new feature flag skeleton |
| `get_flag_prerequisites` | Check flag dependencies |

## Examples

Ask Claude:

> "What projects do I have in LaunchDarkly?"

> "List my feature flags in the production environment"

> "Turn on the `new-checkout` flag in staging"

> "Who made changes to the `dark-mode` flag in the last week?"

> "Add user `alice@example.com` to the beta flag targeting"

## Development

```bash
git clone https://github.com/your-org/launchdarkly-mcp-server
cd launchdarkly-mcp-server
uv venv
uv pip install -e ".[dev]"
```

Run tests:

```bash
uv run pytest
```

## Architecture

```
AI Assistant ── MCP (stdio) ──► launchdarkly-mcp-server ── HTTPS ──► LaunchDarkly API
```

Built with [fastmcp](https://github.com/jlowin/fastmcp) (Python).

## License

MIT
