# Prompt Caching

Cache large, repeated context to cut costs and latency — so you can build
richer experiences without paying for the same tokens over and over.

## What It Is

Prompt caching lets you mark parts of your prompt that don't change between
requests. The first time, Claude processes and caches that content. On
subsequent requests, cached content is read at a fraction of the cost and
near-zero latency.

**Why it matters:** The most useful AI applications need rich context —
a student's learning history, a community's resource database, a long
document being analyzed. Without caching, every request re-processes all
of that, making it expensive and slow. Caching makes it affordable to give
Claude the full picture.

## Setup

```bash
pip install anthropic
```

No special configuration needed — caching is available on all current models.

## How It Works

1. Add `cache_control: {"type": "ephemeral"}` to content you want cached
2. First request: Claude processes and caches that content (cache write)
3. Subsequent requests within 5 minutes: cached content is read instantly
4. Cache TTL refreshes with each hit (5-minute sliding window)

## Basic Usage

```python
import anthropic

client = anthropic.Anthropic()

# A large system prompt you'll reuse across many requests
community_guidelines = open("community_guidelines.txt").read()  # ~10K tokens

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": community_guidelines,
            "cache_control": {"type": "ephemeral"},  # Cache this
        }
    ],
    messages=[
        {"role": "user", "content": "How should we handle a noise complaint?"}
    ],
)
```

The first call writes the cache. Subsequent calls with the same system
prompt read from cache — 90% cheaper for the cached portion.

## What Can Be Cached

| Content Type | How to Cache |
|---|---|
| System prompt | Add `cache_control` to system content blocks |
| User messages | Add `cache_control` to message content blocks |
| Tool definitions | Add `cache_control` to the last tool in the list |
| Images | Add `cache_control` to image content blocks |
| Documents/PDFs | Add `cache_control` to document content blocks |

**Minimum token requirements:**

| Model | Minimum Cacheable Tokens |
|---|---|
| Claude Opus 4 | 1,024 |
| Claude Sonnet 4 | 1,024 |
| Claude Haiku 4 | 1,024 |

Content below the minimum won't be cached (no error, just no caching).

## Cache Breakpoints

You can set up to **4 cache breakpoints** per request. Place them
strategically at the end of content that stays stable:

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": long_reference_document,
            "cache_control": {"type": "ephemeral"},  # Breakpoint 1
        }
    ],
    tools=[
        tool_a,
        tool_b,
        {
            **tool_c,
            "cache_control": {"type": "ephemeral"},  # Breakpoint 2
        },
    ],
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": conversation_history,
                    "cache_control": {"type": "ephemeral"},  # Breakpoint 3
                }
            ],
        },
        {"role": "assistant", "content": "..."},
        {"role": "user", "content": "Follow-up question"},
    ],
)
```

**Important:** Cache matching is prefix-based. Everything up to and
including a breakpoint must match exactly for a cache hit.

## Reading Cache Performance

Check the `usage` field in the response:

```python
print(f"Cache write: {response.usage.cache_creation_input_tokens} tokens")
print(f"Cache read:  {response.usage.cache_read_input_tokens} tokens")
print(f"Uncached:    {response.usage.input_tokens} tokens")
```

- **cache_creation_input_tokens** — tokens written to cache (first request)
- **cache_read_input_tokens** — tokens read from cache (subsequent requests)
- **input_tokens** — tokens processed without caching

## Pricing

| Token Type | Cost vs. Base Input Price |
|---|---|
| Cache write | 25% more than base |
| Cache read | 90% less than base |
| Uncached | Base price |

A cache write pays for itself after just **2 cache reads**.

## Multi-Turn Conversation Pattern

Cache the growing conversation history so each turn only processes new content:

```python
def chat(conversation: list, new_message: str) -> str:
    # Cache everything up to the last exchange
    messages = []

    if len(conversation) > 0:
        # Cache all previous turns as a block
        history = "\n".join(
            f"{'Human' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
            for m in conversation
        )
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Previous conversation:\n{history}",
                    "cache_control": {"type": "ephemeral"},
                },
                {
                    "type": "text",
                    "text": new_message,
                },
            ],
        })
    else:
        messages.append({"role": "user", "content": new_message})

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=[{
            "type": "text",
            "text": "You are a helpful community assistant.",
            "cache_control": {"type": "ephemeral"},
        }],
        messages=messages,
    )

    return response.content[0].text
```

## Caching Tools

Cache your tool definitions to avoid re-processing them each turn:

```python
tools = [
    {"name": "search_resources", "description": "...", "input_schema": {...}},
    {"name": "get_details", "description": "...", "input_schema": {...}},
    {
        "name": "register",
        "description": "...",
        "input_schema": {...},
        "cache_control": {"type": "ephemeral"},  # Cache ALL tools up to here
    },
]
```

## Caching Documents

Perfect for applications that analyze or answer questions about long documents:

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_base64,
                    },
                    "cache_control": {"type": "ephemeral"},
                },
                {
                    "type": "text",
                    "text": "What accessibility accommodations does this policy require?",
                },
            ],
        }
    ],
)
```

## Best Practices

- **Put stable content first.** Cache matching is prefix-based — changing
  anything before a breakpoint invalidates it.
- **Order: system → tools → static messages → dynamic messages.** This
  maximizes cache reuse since stable content stays at the prefix.
- **Cache large content.** The bigger the cached content, the bigger the
  savings. Caching a 100-token prompt saves pennies; caching a 50K-token
  document saves dollars.
- **Monitor hit rates.** Track `cache_read_input_tokens` vs
  `cache_creation_input_tokens` over time. Low hit rates mean your cache
  is being invalidated too often.
- **Use for repeated reference material.** System prompts, tool definitions,
  long documents, conversation history — anything that stays the same across
  multiple requests.
- **Don't cache content that changes every request.** The write cost (1.25x)
  means caching only saves money if the content is reused.

## Changelog

- 2026-04-16: Initial version covering cache breakpoints, pricing, multi-turn
  patterns, and document caching.
