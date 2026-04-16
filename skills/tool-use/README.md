# Tool Use

Give Claude the ability to call functions in your application — bridging
conversation and action so people can get real things done through natural language.

## What It Is

Tool use (function calling) lets you define functions that Claude can invoke
during a conversation. Claude decides when a tool is needed, returns structured
input for the call, and you execute it and return the result. This turns Claude
from a text-in/text-out model into an agent that can look things up, take actions,
and interact with the real world.

**Why it matters:** Tool use is what makes AI actually useful in people's lives.
It's the difference between Claude *telling* someone about a community garden
and Claude *signing them up* for one.

## Setup

```bash
pip install anthropic
```

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Defining Tools

Tools are defined as JSON schemas describing the function name, purpose, and parameters:

```python
tools = [
    {
        "name": "search_community_events",
        "description": "Search for local community events by topic, date range, and location. Returns upcoming events that match the criteria.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The type of event to search for, e.g. 'volunteer cleanup', 'language exchange', 'open mic'"
                },
                "location": {
                    "type": "string",
                    "description": "City or neighborhood to search in"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of events to return",
                    "default": 5
                }
            },
            "required": ["topic", "location"]
        }
    }
]
```

**Tips for good tool definitions:**
- Write descriptions as if explaining to a thoughtful colleague
- Include examples of valid values in parameter descriptions
- Mark only truly required fields as `required`
- Use `enum` when there's a fixed set of valid values

## The Tool Use Loop

```python
import anthropic
import json

client = anthropic.Anthropic()

def handle_tool_call(name: str, input: dict) -> str:
    """Route tool calls to your actual implementations."""
    if name == "search_community_events":
        return search_events(input["topic"], input["location"])
    if name == "register_for_event":
        return register(input["event_id"], input["attendee_name"])
    return json.dumps({"error": f"Unknown tool: {name}"})

messages = [
    {"role": "user", "content": "Find volunteer events near me in Portland this weekend"}
]

# Loop until Claude responds without tool calls
while True:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        tools=tools,
        messages=messages,
    )

    messages.append({"role": "assistant", "content": response.content})

    if response.stop_reason == "end_turn":
        # Claude is done — extract final text
        for block in response.content:
            if hasattr(block, "text"):
                print(block.text)
        break

    # Process tool calls
    tool_results = []
    for block in response.content:
        if block.type == "tool_use":
            result = handle_tool_call(block.name, block.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result,
            })

    messages.append({"role": "user", "content": tool_results})
```

## Controlling Tool Choice

By default, Claude decides whether to use tools (`"auto"`). You can override this:

```python
# Force Claude to use a specific tool
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=tools,
    tool_choice={"type": "tool", "name": "search_community_events"},
    messages=messages,
)

# Force Claude to use *some* tool (any of them)
tool_choice={"type": "any"}

# Let Claude decide (default)
tool_choice={"type": "auto"}

# Disable tool use for this turn
tool_choice={"type": "none"}
```

Use `"tool"` with a specific name when you know which function should run (e.g.,
the user explicitly asked to search). Use `"auto"` when Claude should judge
whether a tool is needed.

## Handling Errors

Return errors as tool results so Claude can adapt:

```python
tool_results.append({
    "type": "tool_result",
    "tool_use_id": block.id,
    "content": json.dumps({"error": "No events found for that date range"}),
    "is_error": True,
})
```

When `is_error` is `True`, Claude knows the call failed and can try a different
approach, ask the user for clarification, or gracefully explain what happened.

## Parallel Tool Calls

Claude can return multiple `tool_use` blocks in a single response when it
determines that several independent lookups are needed. Always process all
of them before sending results back:

```python
# Claude might return two tool calls at once:
#   1. search_community_events(topic="tutoring", location="Portland")
#   2. search_community_events(topic="mentorship", location="Portland")

tool_results = []
for block in response.content:
    if block.type == "tool_use":
        result = handle_tool_call(block.name, block.input)
        tool_results.append({
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": result,
        })

# Send ALL results back together
messages.append({"role": "user", "content": tool_results})
```

## Streaming Tool Use

For real-time UIs, use streaming to show progress as Claude thinks:

```python
with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=tools,
    messages=messages,
) as stream:
    for event in stream:
        if event.type == "content_block_start":
            if event.content_block.type == "tool_use":
                print(f"Calling: {event.content_block.name}")
        elif event.type == "text":
            print(event.text, end="", flush=True)

    response = stream.get_final_message()
```

## Best Practices

- **Write descriptive tool names and descriptions.** Claude uses these to decide
  when and how to call your tools. Vague descriptions lead to misuse.
- **Validate inputs.** Claude generates structured input, but always validate
  before executing — especially for tools that modify data or cost money.
- **Set iteration limits.** In any tool-use loop, cap iterations (10-20) to
  prevent runaway conversations.
- **Keep tool count reasonable.** Claude handles 10-20 tools well. Beyond that,
  consider grouping related functions or using a routing pattern.
- **Return structured results.** JSON is ideal — Claude can parse and reason
  about structured data better than free text.
- **Design tools for people.** Every tool should ultimately serve a human need.
  Ask: "What does this help someone accomplish?"

## Changelog

- 2026-04-16: Initial version covering tool definitions, the use loop, tool choice,
  error handling, parallel calls, and streaming.
