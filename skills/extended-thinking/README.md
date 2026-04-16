# Extended Thinking

Let Claude reason through hard problems step by step before responding —
the difference between a snap answer and a considered one.

## What It Is

Extended thinking gives Claude a scratchpad to work through complex
problems before producing a final answer. Like a person thinking
carefully before speaking, Claude can explore approaches, check its
work, and refine its reasoning.

**Why it matters:** Some questions deserve more than a quick answer.
When someone asks about treatment options, legal rights, or how to
navigate a complex system, careful reasoning leads to better outcomes.
Extended thinking makes Claude more reliable on the questions that
matter most.

## Setup

```bash
pip install anthropic
```

No beta headers needed — extended thinking is GA on all supported models.

## Basic Usage

### Adaptive Thinking (Recommended)

Claude decides how much to think based on the problem's complexity:

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=16000,
    thinking={"type": "adaptive"},
    messages=[
        {
            "role": "user",
            "content": (
                "A community health center is deciding between two locations. "
                "Site A is centrally located but expensive ($8K/month rent, "
                "ADA compliant). Site B is cheaper ($3K/month) but farther "
                "from public transit and needs $40K in accessibility renovations. "
                "They serve 200 patients/month, 30% rely on public transit, "
                "15% have mobility challenges. Analyze the tradeoffs."
            ),
        }
    ],
)

for block in response.content:
    if block.type == "thinking":
        print(f"[Thinking]\n{block.thinking}\n")
    elif block.type == "text":
        print(f"[Answer]\n{block.text}")
```

### Manual Thinking (Explicit Budget)

Set an exact token budget for thinking:

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=16000,
    thinking={"type": "enabled", "budget_tokens": 10000},
    messages=[{"role": "user", "content": "Complex question here"}],
)
```

## Model Support

| Model | Adaptive Thinking | Manual Thinking |
|---|---|---|
| Claude Opus 4.6 | Yes (recommended) | Yes (deprecated) |
| Claude Sonnet 4.6 | Yes (recommended) | Yes (deprecated) |
| Claude Opus 4.5 | No | Yes |
| Claude Sonnet 4.5 | No | Yes |
| Claude Haiku 4.5 | No | Yes |

Use **adaptive** on models that support it. Use **manual** otherwise.

## Response Structure

Responses include `thinking` blocks before `text` blocks:

```python
for block in response.content:
    if block.type == "thinking":
        # Claude's internal reasoning (may be long)
        print(block.thinking)
        # Cryptographic signature for multi-turn conversations
        print(block.signature)
    elif block.type == "text":
        # The final answer
        print(block.text)
```

## Thinking Display Modes

Control whether thinking content is visible:

```python
# Show thinking (default on Claude 4)
thinking={"type": "adaptive", "display": "summarized"}

# Hide thinking (saves latency, still billed)
thinking={"type": "adaptive", "display": "omitted"}
```

With `"omitted"`, thinking blocks still appear in the response but
with empty `thinking` fields. The `signature` is preserved for
multi-turn use.

## Multi-Turn with Thinking

When using tools or multi-turn conversations, **preserve thinking blocks**:

```python
# Turn 1: Claude thinks and calls a tool
response1 = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=16000,
    thinking={"type": "enabled", "budget_tokens": 10000},
    tools=tools,
    messages=[{"role": "user", "content": "Find accessible clinics near 97201"}],
)

# Turn 2: MUST include thinking blocks from turn 1
messages = [
    {"role": "user", "content": "Find accessible clinics near 97201"},
    {"role": "assistant", "content": response1.content},  # Includes thinking blocks
    {
        "role": "user",
        "content": [{
            "type": "tool_result",
            "tool_use_id": tool_use_block.id,
            "content": tool_result,
        }],
    },
]

response2 = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=16000,
    thinking={"type": "enabled", "budget_tokens": 10000},
    tools=tools,
    messages=messages,
)
```

**Critical:** With tool use, you MUST pass thinking blocks back.
Without tools, thinking blocks from previous turns are optional.

## Streaming Thinking

Show thinking in real-time:

```python
with client.messages.stream(
    model="claude-opus-4-6",
    max_tokens=16000,
    thinking={"type": "adaptive"},
    messages=[{"role": "user", "content": "Complex analysis here"}],
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

## Budget Tokens vs Max Tokens

- `budget_tokens` — how many tokens Claude can use for thinking
- `max_tokens` — total output limit (thinking + answer)
- `budget_tokens` must be less than `max_tokens`
- Minimum budget: 1,024 tokens

**Guidelines:**
- 5,000-10,000: Most tasks
- 16,000-32,000: Genuinely hard reasoning (math proofs, multi-factor analysis)
- Claude won't necessarily use the full budget — it stops when it's done

## When to Use Extended Thinking

**Good for:**
- Multi-step reasoning (math, logic, system design)
- Complex analysis with competing tradeoffs
- Problems where Claude's first instinct might be wrong
- Agentic workflows where careful planning matters
- Anything you'd want a person to think carefully about

**Skip for:**
- Simple factual questions
- Creative writing (unless reasoning about structure)
- Latency-critical applications
- Simple classification or extraction

## Limitations

- `tool_choice` must be `"auto"` or `"none"` — can't force a specific tool
- Thinking tokens are always billed, even with `display: "omitted"`
- Switching between adaptive and manual modes breaks prompt cache
- Adds latency (200-500ms+ depending on budget)

## Changelog

- 2026-04-16: Initial version covering adaptive and manual thinking,
  multi-turn patterns, streaming, and model support matrix.
