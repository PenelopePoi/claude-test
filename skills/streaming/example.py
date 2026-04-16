"""
Streaming - Working Example

A real-time assistant that streams responses while helping people
navigate community resources. Demonstrates: text streaming, tool use
streaming, thinking streaming, and the agentic stream loop.

Requires: pip install anthropic

Usage:
    export ANTHROPIC_API_KEY="sk-ant-..."
    python example.py
"""

import anthropic
import json
import sys


client = anthropic.Anthropic()


# ---------------------------------------------------------------------------
# Tools for the streaming demo
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "lookup_resource",
        "description": (
            "Look up a community resource by category. Categories: "
            "housing, food, health, legal, education, employment."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": [
                        "housing", "food", "health",
                        "legal", "education", "employment",
                    ],
                },
                "zipcode": {
                    "type": "string",
                    "description": "5-digit zip code",
                },
            },
            "required": ["category"],
        },
    },
]

MOCK_RESOURCES = {
    "housing": [
        {
            "name": "Housing Rights Hotline",
            "phone": "(503) 555-0180",
            "description": "Free advice on tenant rights, eviction defense, and fair housing complaints.",
        },
        {
            "name": "Rent Assistance Program",
            "phone": "(503) 555-0181",
            "description": "Emergency rent assistance for households below 50% AMI. Up to 3 months.",
        },
    ],
    "food": [
        {
            "name": "Community Food Share",
            "phone": "(503) 555-0170",
            "description": "Weekly food boxes, no ID required. Tuesdays and Thursdays 10am-2pm.",
        },
    ],
    "health": [
        {
            "name": "Open Door Clinic",
            "phone": "(503) 555-0160",
            "description": "Free primary care, dental, and mental health. Walk-ins Mon-Thu.",
        },
    ],
}


def handle_tool(name: str, input: dict) -> str:
    category = input.get("category", "")
    resources = MOCK_RESOURCES.get(category, [])
    if not resources:
        return json.dumps({"message": f"No resources found for '{category}'"})
    return json.dumps(resources, indent=2)


# ---------------------------------------------------------------------------
# Example 1: Simple text streaming
# ---------------------------------------------------------------------------

def stream_text(question: str) -> None:
    """Stream a plain text response."""

    print("=" * 60)
    print("STREAMING TEXT")
    print("=" * 60)
    print(f"Q: {question}\n")
    print("A: ", end="")

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=(
            "You are a community resource navigator. Give clear, "
            "actionable advice. Keep answers concise."
        ),
        messages=[{"role": "user", "content": question}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)

        message = stream.get_final_message()

    print(f"\n\n[{message.usage.output_tokens} tokens]")


# ---------------------------------------------------------------------------
# Example 2: Streaming with tool use (agentic loop)
# ---------------------------------------------------------------------------

def stream_with_tools(question: str) -> None:
    """Stream responses in an agentic loop with tool calls."""

    print("\n" + "=" * 60)
    print("STREAMING WITH TOOLS")
    print("=" * 60)
    print(f"Q: {question}\n")

    messages = [{"role": "user", "content": question}]
    max_turns = 5

    for turn in range(max_turns):
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=(
                "You help people find community resources. Use the "
                "lookup_resource tool to find specific services, then "
                "explain what you found in a helpful way."
            ),
            tools=TOOLS,
            messages=messages,
        ) as stream:
            # Stream text as it arrives
            for event in stream:
                if event.type == "content_block_start":
                    if event.content_block.type == "tool_use":
                        print(f"\n  [Looking up: {event.content_block.name}...]", end="")
                elif event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        print(event.delta.text, end="", flush=True)

            message = stream.get_final_message()

        messages.append({"role": "assistant", "content": message.content})

        # Process tool calls
        tool_results = []
        for block in message.content:
            if block.type == "tool_use":
                result = handle_tool(block.name, block.input)
                print(f" done")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        if not tool_results:
            break

        messages.append({"role": "user", "content": tool_results})

    print(f"\n\n[{message.usage.output_tokens} tokens]")


# ---------------------------------------------------------------------------
# Example 3: Streaming with extended thinking
# ---------------------------------------------------------------------------

def stream_thinking(question: str) -> None:
    """Stream both thinking and response."""

    print("\n" + "=" * 60)
    print("STREAMING WITH THINKING")
    print("=" * 60)
    print(f"Q: {question}\n")

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=(
            "You help people understand complex policy decisions "
            "that affect their communities. Think carefully before "
            "responding."
        ),
        messages=[{"role": "user", "content": question}],
    ) as stream:
        current_type = None
        for event in stream:
            if event.type == "content_block_start":
                new_type = event.content_block.type
                if new_type != current_type:
                    current_type = new_type
                    if new_type == "thinking":
                        print("[Reasoning...]")
                    elif new_type == "text":
                        print("\n[Answer]")

            elif event.type == "content_block_delta":
                if event.delta.type == "thinking_delta":
                    # Show thinking with dimmer formatting
                    print(event.delta.thinking, end="", flush=True)
                elif event.delta.type == "text_delta":
                    print(event.delta.text, end="", flush=True)

        message = stream.get_final_message()

    print(f"\n\n[{message.usage.output_tokens} tokens]")


# ---------------------------------------------------------------------------
# Example questions
# ---------------------------------------------------------------------------

EXAMPLES = {
    "text": (
        "My landlord just told me I have 30 days to move out, but I've "
        "been paying rent on time for 3 years. What are my rights?"
    ),
    "tools": (
        "I lost my job last week and I'm worried about paying rent and "
        "feeding my kids. What help is available?"
    ),
    "thinking": (
        "Our city is considering a new zoning law that would allow "
        "more multi-family housing in single-family neighborhoods. "
        "What are the implications for current residents, housing "
        "affordability, and community character?"
    ),
}


def main():
    stream_text(EXAMPLES["text"])
    stream_with_tools(EXAMPLES["tools"])
    stream_thinking(EXAMPLES["thinking"])


if __name__ == "__main__":
    main()
