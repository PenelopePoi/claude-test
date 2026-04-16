"""
Extended Thinking - Working Example

An advisor that carefully reasons through complex community decisions.
Demonstrates: adaptive thinking, thinking display, streaming thinking,
and budget control.

Requires: pip install anthropic

Usage:
    export ANTHROPIC_API_KEY="sk-ant-..."
    python example.py
"""

import anthropic


client = anthropic.Anthropic()


# ---------------------------------------------------------------------------
# Example 1: Adaptive thinking for a complex decision
# ---------------------------------------------------------------------------

def analyze_decision(scenario: str) -> None:
    """Use extended thinking to carefully analyze a community decision."""

    print("=" * 60)
    print("EXTENDED THINKING: Community Decision Analysis")
    print("=" * 60)

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=(
            "You are an advisor helping community organizations make "
            "well-reasoned decisions. Consider all stakeholders, especially "
            "those who are often overlooked — people with disabilities, "
            "non-English speakers, low-income residents, elderly, and "
            "youth. Show your reasoning clearly."
        ),
        messages=[{"role": "user", "content": scenario}],
    )

    for block in response.content:
        if block.type == "thinking":
            print(f"\n--- Reasoning Process ({len(block.thinking)} chars) ---")
            # Show first 500 chars of thinking
            preview = block.thinking[:500]
            if len(block.thinking) > 500:
                preview += f"\n... [{len(block.thinking) - 500} more chars]"
            print(preview)
        elif block.type == "text":
            print(f"\n--- Recommendation ---")
            print(block.text)

    # Show token usage
    usage = response.usage
    print(f"\n--- Token Usage ---")
    print(f"Input: {usage.input_tokens}")
    print(f"Output: {usage.output_tokens}")


# ---------------------------------------------------------------------------
# Example 2: Streaming thinking in real-time
# ---------------------------------------------------------------------------

def stream_analysis(question: str) -> None:
    """Stream thinking and answer in real-time."""

    print("\n" + "=" * 60)
    print("STREAMING EXTENDED THINKING")
    print("=" * 60)

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=16000,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": question}],
    ) as stream:
        current_block = None
        for event in stream:
            if event.type == "content_block_start":
                block_type = event.content_block.type
                if block_type != current_block:
                    current_block = block_type
                    if block_type == "thinking":
                        print("\n[Thinking...]")
                    elif block_type == "text":
                        print("\n\n[Answer]")
            elif event.type == "content_block_delta":
                if event.delta.type == "thinking_delta":
                    print(event.delta.thinking, end="", flush=True)
                elif event.delta.type == "text_delta":
                    print(event.delta.text, end="", flush=True)

    print()


# ---------------------------------------------------------------------------
# Example 3: Manual budget for controlled reasoning
# ---------------------------------------------------------------------------

def quick_vs_deep(question: str) -> None:
    """Compare responses with different thinking budgets."""

    print("\n" + "=" * 60)
    print("QUICK vs DEEP THINKING")
    print("=" * 60)

    for label, budget in [("Quick (2K budget)", 2000), ("Deep (10K budget)", 10000)]:
        print(f"\n--- {label} ---")

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=16000,
            thinking={"type": "enabled", "budget_tokens": budget},
            messages=[{"role": "user", "content": question}],
        )

        thinking_tokens = 0
        for block in response.content:
            if block.type == "thinking":
                thinking_tokens = len(block.thinking.split())
            elif block.type == "text":
                print(block.text[:300])
                if len(block.text) > 300:
                    print(f"... [{len(block.text) - 300} more chars]")

        print(f"  (Thinking used ~{thinking_tokens} words)")


# ---------------------------------------------------------------------------
# Example scenarios
# ---------------------------------------------------------------------------

SCENARIOS = {
    "site_selection": (
        "Our community health center needs to choose between two sites:\n\n"
        "Site A: Downtown, $8,000/month rent. Fully ADA compliant. On two "
        "bus lines. 800 sq ft. Street parking only.\n\n"
        "Site B: East side, $3,500/month rent. Needs $45,000 in accessibility "
        "renovations (ramp, bathroom, door widths). 1,400 sq ft. Has a "
        "parking lot. Nearest bus stop is 0.4 miles away.\n\n"
        "We serve ~200 patients/month. 30% rely on public transit. 15% have "
        "mobility challenges. 40% speak Spanish as primary language (nearby "
        "Site B has a larger Spanish-speaking population). Our annual budget "
        "for rent is $60,000.\n\n"
        "Which site should we choose? Consider a 3-year horizon."
    ),

    "program_funding": (
        "We have $25,000 to fund ONE new program at our community center. "
        "Three proposals:\n\n"
        "1. After-school tutoring (K-8): Would serve ~40 kids/semester. "
        "Needs $20K for tutors, $5K for supplies. Local university will "
        "provide volunteer tutors if we cover coordination.\n\n"
        "2. Senior digital literacy: Would serve ~60 seniors/year. "
        "Needs $15K for instructors, $10K for loaner tablets. Could "
        "apply for matching grant next year.\n\n"
        "3. Community garden + nutrition education: Would serve ~100 "
        "families. Needs $12K for garden setup, $8K for nutrition "
        "educator, $5K for first year seeds/tools. Produces food "
        "that offsets food bank costs.\n\n"
        "Which should we fund? Our neighborhood has 22% child poverty, "
        "35% of seniors live alone, and the nearest grocery store is "
        "2 miles away."
    ),

    "accessibility_audit": (
        "Review this event plan for accessibility gaps:\n\n"
        "Annual Community Fair — Saturday 10am-4pm at Riverside Park\n"
        "- 15 vendor booths along the main path (gravel)\n"
        "- Live music stage with seating area (folding chairs on grass)\n"
        "- Children's activities zone\n"
        "- Food trucks (3, parked on asphalt lot)\n"
        "- Information booth for social services\n"
        "- Free health screenings (blood pressure, vision, dental)\n"
        "- Porta-potties at north end of park\n"
        "- Parking in adjacent lot (50 spaces)\n"
        "- Expected attendance: 500-800 people\n\n"
        "What accessibility issues do you see, and how should we fix them?"
    ),
}


def main():
    # Run the site selection analysis with full thinking
    analyze_decision(SCENARIOS["site_selection"])

    # Stream the accessibility audit
    stream_analysis(SCENARIOS["accessibility_audit"])


if __name__ == "__main__":
    main()
