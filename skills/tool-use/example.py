"""
Tool Use - Working Example

An agent that helps people find and sign up for community events.
Demonstrates: tool definitions, the agentic loop, error handling,
and parallel tool calls.

Requires: pip install anthropic

Usage:
    export ANTHROPIC_API_KEY="sk-ant-..."
    python example.py
"""

import anthropic
import json


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "search_community_events",
        "description": (
            "Search for community events by topic and location. "
            "Returns a list of upcoming events with name, date, "
            "description, and registration link."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": (
                        "Type of event, e.g. 'volunteer cleanup', "
                        "'language exchange', 'tutoring', 'open mic'"
                    ),
                },
                "location": {
                    "type": "string",
                    "description": "City or neighborhood",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Max events to return (default 5)",
                },
            },
            "required": ["topic", "location"],
        },
    },
    {
        "name": "get_event_details",
        "description": (
            "Get full details for a specific event including "
            "accessibility info, transit options, and what to bring."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "The event identifier",
                },
            },
            "required": ["event_id"],
        },
    },
    {
        "name": "register_for_event",
        "description": (
            "Register a person for a community event. "
            "Returns confirmation details."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "The event to register for",
                },
                "name": {
                    "type": "string",
                    "description": "Full name of the attendee",
                },
                "accessibility_needs": {
                    "type": "string",
                    "description": (
                        "Any accessibility requirements "
                        "(wheelchair access, ASL interpreter, etc.)"
                    ),
                },
            },
            "required": ["event_id", "name"],
        },
    },
]


# ---------------------------------------------------------------------------
# Mock implementations (replace with real APIs)
# ---------------------------------------------------------------------------

MOCK_EVENTS = [
    {
        "id": "evt-001",
        "name": "Riverside Park Cleanup",
        "date": "2026-04-20",
        "time": "9:00 AM",
        "location": "Riverside Park, Portland",
        "description": (
            "Join neighbors to clean up the riverbank. Gloves and bags "
            "provided. All ages welcome. Followed by a community picnic."
        ),
        "spots_remaining": 12,
    },
    {
        "id": "evt-002",
        "name": "Free ESL Conversation Circle",
        "date": "2026-04-22",
        "time": "6:30 PM",
        "location": "Multnomah County Library, Portland",
        "description": (
            "Practice English in a relaxed, supportive group. Native "
            "speakers volunteer as conversation partners. Childcare available."
        ),
        "spots_remaining": 8,
    },
    {
        "id": "evt-003",
        "name": "Youth Mentorship Kickoff",
        "date": "2026-04-25",
        "time": "10:00 AM",
        "location": "Community Center, SE Portland",
        "description": (
            "Orientation for new mentors. Learn how to support a young "
            "person through weekly 1-on-1 sessions focused on their goals."
        ),
        "spots_remaining": 5,
    },
]


def search_events(topic: str, location: str, max_results: int = 5) -> str:
    """Search mock events database."""
    # In production, this would call a real events API
    results = [e for e in MOCK_EVENTS if location.lower() in e["location"].lower()]
    return json.dumps(results[:max_results], indent=2)


def get_details(event_id: str) -> str:
    """Get details for a specific event."""
    for event in MOCK_EVENTS:
        if event["id"] == event_id:
            details = {
                **event,
                "accessibility": "Wheelchair accessible. ASL interpreter available on request.",
                "transit": "Bus lines 15, 44 stop within 2 blocks. Bike parking available.",
                "what_to_bring": "Water bottle, sunscreen. All other supplies provided.",
            }
            return json.dumps(details, indent=2)
    return json.dumps({"error": f"Event {event_id} not found"})


def register(event_id: str, name: str, accessibility_needs: str = "") -> str:
    """Register for an event."""
    for event in MOCK_EVENTS:
        if event["id"] == event_id:
            return json.dumps({
                "confirmation": f"CONF-{event_id[-3:]}-{name[:3].upper()}",
                "event": event["name"],
                "date": event["date"],
                "message": f"You're registered, {name}! See you there.",
                "accessibility_note": (
                    f"We've noted your needs: {accessibility_needs}. "
                    "The organizer will follow up."
                    if accessibility_needs
                    else ""
                ),
            }, indent=2)
    return json.dumps({"error": f"Event {event_id} not found"})


# ---------------------------------------------------------------------------
# Tool call router
# ---------------------------------------------------------------------------

def handle_tool_call(name: str, tool_input: dict) -> str:
    """Route tool calls to implementations."""
    if name == "search_community_events":
        return search_events(
            tool_input["topic"],
            tool_input["location"],
            tool_input.get("max_results", 5),
        )
    if name == "get_event_details":
        return get_details(tool_input["event_id"])
    if name == "register_for_event":
        return register(
            tool_input["event_id"],
            tool_input["name"],
            tool_input.get("accessibility_needs", ""),
        )
    return json.dumps({"error": f"Unknown tool: {name}"})


# ---------------------------------------------------------------------------
# Agentic loop
# ---------------------------------------------------------------------------

MAX_ITERATIONS = 10

SYSTEM_PROMPT = """You are a friendly community assistant that helps people
find and join local events. When searching, cast a wide net — look for
different related topics if the first search doesn't find enough options.
Always mention accessibility information and transit options when sharing
event details. Confirm with the person before registering them."""


def run(user_message: str) -> None:
    """Run the tool-use agent loop."""
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": user_message}]

    print(f"User: {user_message}")
    print("-" * 60)

    for i in range(1, MAX_ITERATIONS + 1):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        # Process response blocks
        tool_results = []
        for block in response.content:
            if hasattr(block, "text"):
                print(f"\nAssistant: {block.text}")

            elif block.type == "tool_use":
                print(f"\n  [{block.name}({json.dumps(block.input, indent=2)})]")
                result = handle_tool_call(block.name, block.input)
                print(f"  -> {result[:120]}...")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        if not tool_results:
            print("\n" + "=" * 60)
            return

        messages.append({"role": "user", "content": tool_results})

    print(f"\nStopped after {MAX_ITERATIONS} iterations.")


# ---------------------------------------------------------------------------
# Example tasks
# ---------------------------------------------------------------------------

EXAMPLE_TASKS = [
    # Community - connecting people to their neighbors
    "I just moved to Portland and don't know anyone. "
    "What volunteer events are happening this month?",

    # Accessibility - making sure everyone can participate
    "I'd like to join a community event this weekend. "
    "I use a wheelchair — can you find something accessible?",

    # Learning - helping someone grow
    "My mom is learning English and wants to practice conversation "
    "with native speakers. Anything like that in Portland?",

    # Mentorship - paying it forward
    "I want to mentor a young person. How do I get started?",
]

if __name__ == "__main__":
    run(EXAMPLE_TASKS[0])
