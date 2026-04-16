# MCP Servers

Build servers that give Claude access to your data, APIs, and tools using
the Model Context Protocol — so anyone can extend what Claude can do.

## What It Is

MCP (Model Context Protocol) is a standard for connecting AI applications
to external services. You build an MCP server, Claude connects to it, and
suddenly Claude can search your database, call your APIs, or read your files.

Think of it like building a web API, but designed specifically for LLMs.

**Why it matters:** MCP democratizes what Claude can do. Instead of waiting for
Anthropic to add an integration, anyone can build one — connecting Claude to
their local library catalog, community health database, neighborhood alert
system, or whatever their community needs.

**Architecture:**

```
Host (Claude Desktop / Claude Code / your app)
  └── Client (speaks MCP protocol)
        └── Server (your code — exposes tools, resources, prompts)
```

## Setup

```bash
pip install "mcp[cli]"
```

Requires Python 3.10+.

## Core Concepts

MCP servers expose three primitives:

| Primitive | Purpose | Analogy |
|---|---|---|
| **Tools** | Actions Claude can take | POST endpoints |
| **Resources** | Data Claude can read | GET endpoints |
| **Prompts** | Reusable interaction templates | Saved queries |

## Building a Server with FastMCP

FastMCP is the high-level API built into the MCP SDK. It uses decorators
to reduce boilerplate:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("community_events")

@mcp.tool()
def search_events(topic: str, zipcode: str) -> str:
    """Find community events by topic near a zipcode."""
    # Your implementation here
    return '{"events": [...]}'

@mcp.resource("events://upcoming")
def upcoming_events() -> str:
    """List all upcoming events."""
    return '{"events": [...]}'

@mcp.prompt(name="event_recommendation", description="Suggest events for someone")
def recommend_prompt(interests: str, availability: str) -> str:
    return (
        f"Based on these interests: {interests}\n"
        f"And this availability: {availability}\n"
        f"Recommend community events that would be a good fit."
    )

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### Tools

Tools let Claude take actions. Define them with `@mcp.tool()`:

```python
from pydantic import BaseModel

class TranslationRequest(BaseModel):
    text: str
    source_language: str
    target_language: str

@mcp.tool()
def translate_text(request: TranslationRequest) -> str:
    """Translate text between languages to help people communicate."""
    # Call your translation API
    return translated_text
```

FastMCP automatically generates the JSON schema from type hints and
docstrings. Use Pydantic models for complex inputs.

### Resources

Resources expose data for Claude to read:

```python
# Static resource
@mcp.resource("guides://accessibility-checklist")
def accessibility_checklist() -> str:
    """Community accessibility checklist."""
    return load_checklist()

# Dynamic resource with URI template
@mcp.resource("members://{member_id}/profile")
def member_profile(member_id: str) -> str:
    """Look up a community member's profile."""
    return get_profile(member_id)
```

### Prompts

Prompts are reusable templates that guide Claude's behavior:

```python
@mcp.prompt(
    name="write_welcome_letter",
    description="Draft a welcome letter for a new community member"
)
def welcome_letter(name: str, neighborhood: str, interests: str) -> str:
    return (
        f"Write a warm, personal welcome letter to {name} who just moved "
        f"to {neighborhood}. They're interested in {interests}. Mention "
        f"specific local resources and upcoming events related to their "
        f"interests. Keep it under 200 words."
    )
```

## Connecting to Claude

### Claude Code

```bash
# Add a local stdio server
claude mcp add community-events -- python /path/to/server.py

# Add with environment variables
claude mcp add community-events \
  --env DB_URL=postgres://localhost/events \
  -- python /path/to/server.py

# Add a remote HTTP server
claude mcp add --transport http remote-api https://api.example.com/mcp

# Check status
claude mcp list

# Remove
claude mcp remove community-events
```

### Claude Desktop

Edit `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "community-events": {
      "type": "stdio",
      "command": "python",
      "args": ["/path/to/server.py"],
      "env": {
        "DB_URL": "postgres://localhost/events"
      }
    }
  }
}
```

### Scope Options (Claude Code)

| Scope | Stored In | Shared? |
|---|---|---|
| `local` | `~/.claude.json` | No (your machine only) |
| `project` | `.mcp.json` in repo | Yes (team via git) |
| `user` | `~/.claude.json` | No (all your projects) |

Use `project` scope for servers your whole team should have:
```bash
claude mcp add --scope project shared-db -- python db_server.py
```

## Transport Mechanisms

| Transport | When to Use | How |
|---|---|---|
| **stdio** | Local servers | `mcp.run(transport="stdio")` |
| **HTTP** | Remote/cloud servers | `mcp.run(transport="streamable-http")` |
| **SSE** | Legacy (deprecated) | `mcp.run(transport="sse")` |

Use **stdio** for local tools. Use **HTTP** when the server runs on a
different machine or as a cloud service.

## Low-Level API

For full control, use the Server class directly:

```python
from mcp.server import Server
import mcp.types as types

server = Server("my_server")

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="find_tutor",
            description="Find a volunteer tutor for a student",
            inputSchema={
                "type": "object",
                "properties": {
                    "subject": {"type": "string"},
                    "grade_level": {"type": "integer"},
                    "language": {"type": "string", "default": "English"},
                },
                "required": ["subject", "grade_level"],
            },
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "find_tutor":
        tutor = find_matching_tutor(**arguments)
        return [types.TextContent(type="text", text=str(tutor))]
    raise ValueError(f"Unknown tool: {name}")
```

## Best Practices

- **Write clear tool descriptions.** Claude decides when to use your tools
  based on the description. Vague descriptions = wrong tool calls.
- **Validate inputs.** Never trust that Claude sent correct data — validate
  everything, especially for tools that write or spend money.
- **Keep servers focused.** One server per domain (events, translations,
  member profiles) is easier to maintain than one monolith.
- **Use project scope for teams.** Commit `.mcp.json` so everyone gets
  the same tools.
- **Return structured data.** JSON responses let Claude reason about
  results more effectively than free text.
- **Set output limits for large responses.** Use `_meta.anthropic/maxResultSizeChars`
  for tools that might return large payloads.
- **Design tools that serve people.** Every tool should help someone
  accomplish something real — learning, connecting, creating, accessing
  services they need.

## Changelog

- 2026-04-16: Initial version covering FastMCP, low-level API, transport
  mechanisms, and Claude Desktop/Code configuration.
