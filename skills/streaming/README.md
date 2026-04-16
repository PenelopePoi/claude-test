# Streaming

Show Claude's response as it's generated — word by word — so people
aren't staring at a blank screen wondering if anything is happening.

## What It Is

Streaming delivers Claude's response incrementally via Server-Sent Events
(SSE). Instead of waiting for the complete response, your application
receives and displays text as it's generated. This makes interactions
feel fast and natural, even for long responses.

**Why it matters:** When someone asks for help navigating healthcare
options or understanding their rights, they shouldn't wait 10 seconds
staring at nothing. Streaming shows progress immediately and lets people
start reading while Claude is still thinking.

## Setup

```bash
pip install anthropic
```

## Basic Streaming

### Text Stream (Simplest)

```python
import anthropic

client = anthropic.Anthropic()

with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "What resources exist for first-generation college students?",
        }
    ],
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

`stream.text_stream` yields text chunks as they arrive. That's it —
three lines for real-time output.

### Get the Final Message

After streaming, you can access the complete message:

```python
with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=messages,
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)

    # Full message with usage stats
    message = stream.get_final_message()
    print(f"\nTokens used: {message.usage.output_tokens}")
```

## Event Types

When iterating the stream directly (not `text_stream`), you get
structured events:

| Event | When | Contains |
|---|---|---|
| `message_start` | Stream begins | Message ID, model |
| `content_block_start` | New block begins | Block type (text, tool_use, thinking) |
| `content_block_delta` | Content arriving | Text chunk, JSON chunk, or thinking chunk |
| `content_block_stop` | Block complete | Final block content |
| `message_delta` | Message metadata | Stop reason, usage |
| `message_stop` | Stream done | — |
| `ping` | Keep-alive | — (ignore) |

### Processing Raw Events

```python
with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=messages,
) as stream:
    for event in stream:
        if event.type == "content_block_delta":
            if event.delta.type == "text_delta":
                print(event.delta.text, end="", flush=True)

        elif event.type == "message_delta":
            print(f"\nStop reason: {event.delta.stop_reason}")
```

## Streaming with Tools

When Claude calls a tool, tool inputs stream as JSON fragments:

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

        elif event.type == "content_block_delta":
            if event.delta.type == "text_delta":
                print(event.delta.text, end="", flush=True)
            elif event.delta.type == "input_json_delta":
                pass  # Partial JSON — don't parse until block_stop

    # After streaming, get the full parsed tool inputs
    message = stream.get_final_message()
    for block in message.content:
        if block.type == "tool_use":
            print(f"Tool: {block.name}, Input: {block.input}")
```

**Important:** `input_json_delta` gives you partial JSON strings.
Don't try to parse them — wait for `content_block_stop` or use
`get_final_message()` to get the fully parsed input.

## Streaming with Extended Thinking

```python
with client.messages.stream(
    model="claude-opus-4-6",
    max_tokens=16000,
    thinking={"type": "adaptive"},
    messages=messages,
) as stream:
    for event in stream:
        if event.type == "content_block_start":
            if event.content_block.type == "thinking":
                print("[Thinking...]")
            elif event.content_block.type == "text":
                print("\n[Answer]")

        elif event.type == "content_block_delta":
            if event.delta.type == "thinking_delta":
                print(event.delta.thinking, end="", flush=True)
            elif event.delta.type == "text_delta":
                print(event.delta.text, end="", flush=True)
```

## Async Streaming

For web servers and async applications:

```python
from anthropic import AsyncAnthropic

async_client = AsyncAnthropic()

async def stream_response(user_message: str):
    async with async_client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        async for text in stream.text_stream:
            yield text  # Send to your web framework
```

## Stream Helper Methods

The SDK's stream object provides convenience methods:

| Method | Returns | Description |
|---|---|---|
| `stream.text_stream` | Iterator of strings | Just the text chunks |
| `stream.get_final_message()` | `Message` | Complete message after stream ends |
| `stream.get_final_text()` | `str` | Concatenated text after stream ends |
| `stream.until_done()` | None | Block until stream completes |
| `stream.close()` | None | Abort the stream |

## Raw SSE (Low-Level)

For minimal memory usage, use `stream=True` on `create()`:

```python
stream = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=messages,
    stream=True,
)

for event in stream:
    if event.type == "content_block_delta" and event.delta.type == "text_delta":
        print(event.delta.text, end="", flush=True)
```

This doesn't accumulate the final message — lower memory, but you
handle everything yourself.

## Error Handling

```python
import anthropic

try:
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)

except anthropic.APIConnectionError:
    print("Network error — check your connection")
except anthropic.RateLimitError:
    print("Rate limited — wait and retry")
except anthropic.APIStatusError as e:
    print(f"API error {e.status_code}: {e.message}")
```

## Best Practices

- **Always use the context manager** (`with ... as stream`). It ensures
  cleanup even if your code throws an exception.
- **Print with `flush=True`** so text appears immediately, not buffered.
- **Use `text_stream`** for simple text output. Only process raw events
  when you need to handle tools, thinking, or custom UI.
- **Don't parse partial JSON.** Tool input arrives as fragments. Wait
  for the block to finish before parsing.
- **Stream large responses.** For `max_tokens` above ~4096, streaming
  avoids HTTP timeout issues and gives better UX.
- **Show typing indicators.** In chat UIs, show that Claude is working
  as soon as the stream starts, before any text arrives.

## Changelog

- 2026-04-16: Initial version covering text streaming, tool use streaming,
  thinking streaming, async patterns, and error handling.
