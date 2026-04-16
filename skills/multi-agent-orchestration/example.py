"""
Multi-Agent Orchestration - Working Example

Coordinates multiple Claude agents to review a community proposal from
different perspectives, then synthesizes their input into a single assessment.

Demonstrates: orchestrator-worker pattern, parallel fan-out, context passing.

Requires: pip install anthropic

Usage:
    export ANTHROPIC_API_KEY="sk-ant-..."
    python example.py
"""

import anthropic
import concurrent.futures
import json
import textwrap


client = anthropic.Anthropic()


# ---------------------------------------------------------------------------
# Core agent function
# ---------------------------------------------------------------------------

def call_agent(
    system_prompt: str,
    task: str,
    model: str = "claude-sonnet-4-6",
    max_tokens: int = 1500,
) -> str:
    """Run a single agent and return its text response."""
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": task}],
    )
    return "".join(
        block.text for block in response.content if hasattr(block, "text")
    )


# ---------------------------------------------------------------------------
# Pattern 1: Parallel review (fan-out + synthesize)
# ---------------------------------------------------------------------------

REVIEWERS = [
    {
        "name": "Community Impact",
        "system": (
            "You review proposals from the perspective of community impact. "
            "Consider: Who benefits? Who might be excluded? What are the "
            "long-term effects on neighborhood cohesion, local economy, and "
            "social trust? Be specific about populations affected."
        ),
    },
    {
        "name": "Practical Feasibility",
        "system": (
            "You review proposals for practical feasibility. Consider: "
            "What resources, budget, and timeline are needed? What could go "
            "wrong? What dependencies exist? What's the minimum viable version?"
        ),
    },
    {
        "name": "Accessibility & Inclusion",
        "system": (
            "You review proposals for accessibility and inclusion. Consider: "
            "Does this serve people with disabilities? Non-English speakers? "
            "Different income levels? Elderly residents? People without "
            "reliable transportation or internet?"
        ),
    },
]


def parallel_review(proposal: str) -> str:
    """Get independent reviews from multiple perspectives, then synthesize."""
    print("Fanning out to reviewers...")

    with concurrent.futures.ThreadPoolExecutor() as pool:
        futures = {
            pool.submit(call_agent, r["system"], proposal): r["name"]
            for r in REVIEWERS
        }

        reviews = {}
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            reviews[name] = future.result()
            print(f"  [{name}] done")

    # Synthesize
    review_text = "\n\n".join(
        f"### {name}\n{review}" for name, review in reviews.items()
    )

    print("Synthesizing...")
    return call_agent(
        system_prompt=(
            "You synthesize independent reviews into a single assessment. "
            "Highlight where reviewers agree, flag disagreements, and provide "
            "a clear recommendation with specific, actionable next steps. "
            "Be honest about tradeoffs."
        ),
        task=(
            f"## Original Proposal\n{proposal}\n\n"
            f"## Independent Reviews\n{review_text}"
        ),
        model="claude-sonnet-4-6",
        max_tokens=2000,
    )


# ---------------------------------------------------------------------------
# Pattern 2: Orchestrator-worker (decompose + delegate + synthesize)
# ---------------------------------------------------------------------------

def orchestrate(task: str) -> str:
    """Break a task into subtasks, delegate in parallel, synthesize."""

    # Step 1: Decompose
    print("Decomposing task...")
    plan = call_agent(
        system_prompt=(
            "You are a project coordinator. Break the given task into "
            "2-4 independent subtasks that can be worked on in parallel. "
            "Return ONLY a JSON array of strings. No other text."
        ),
        task=task,
    )

    try:
        subtasks = json.loads(plan)
    except json.JSONDecodeError:
        print(f"Could not parse plan: {plan}")
        return plan

    print(f"Subtasks: {json.dumps(subtasks, indent=2)}")

    # Step 2: Execute in parallel
    worker_prompt = (
        "You are a specialist. Complete your assigned task thoroughly. "
        "Be specific, actionable, and grounded in real-world constraints. "
        "Consider who this work ultimately serves."
    )

    print("Delegating to workers...")
    with concurrent.futures.ThreadPoolExecutor() as pool:
        futures = {
            pool.submit(call_agent, worker_prompt, subtask): subtask
            for subtask in subtasks
        }
        results = {}
        for future in concurrent.futures.as_completed(futures):
            subtask = futures[future]
            results[subtask] = future.result()
            short = subtask[:50] + "..." if len(subtask) > 50 else subtask
            print(f"  [{short}] done")

    # Step 3: Synthesize
    work = "\n\n".join(
        f"## {subtask}\n{result}" for subtask, result in results.items()
    )

    print("Synthesizing...")
    return call_agent(
        system_prompt=(
            "You combine specialist contributions into one coherent response. "
            "Preserve important details, resolve contradictions by noting both "
            "perspectives, and organize the result so it's immediately useful."
        ),
        task=f"## Original Task\n{task}\n\n## Specialist Work\n{work}",
        model="claude-sonnet-4-6",
        max_tokens=2000,
    )


# ---------------------------------------------------------------------------
# Pattern 3: Pipeline (sequential transformation)
# ---------------------------------------------------------------------------

def pipeline(text: str) -> str:
    """Process text through a sequence of specialist agents."""
    stages = [
        {
            "name": "Plain Language",
            "system": (
                "Rewrite the following text in clear, simple language "
                "accessible to someone with an 8th-grade reading level. "
                "Preserve all meaning and important details."
            ),
        },
        {
            "name": "Cultural Sensitivity",
            "system": (
                "Review this text for cultural sensitivity. Flag anything "
                "that assumes a specific cultural context and suggest "
                "alternatives. Return the improved text."
            ),
        },
        {
            "name": "Accessibility",
            "system": (
                "Review this text for accessibility. Ensure it uses clear "
                "structure with headings, avoids jargon and idioms that "
                "might confuse non-native speakers, and works well when "
                "read aloud by a screen reader. Return the final text."
            ),
        },
    ]

    current = text
    for stage in stages:
        print(f"  [{stage['name']}]")
        current = call_agent(stage["system"], current)

    return current


# ---------------------------------------------------------------------------
# Example tasks
# ---------------------------------------------------------------------------

SAMPLE_PROPOSAL = textwrap.dedent("""\
    Proposal: Community Learning Hub

    We propose converting the unused east wing of the Riverside Community
    Center into a free learning hub. The space would offer:

    - Drop-in tutoring for K-12 students (weekdays 3-7pm)
    - ESL conversation circles (weekday evenings)
    - Digital literacy workshops for seniors (Saturday mornings)
    - A quiet study space with free wifi and loaner laptops

    Budget: $45,000 for renovation, $30,000/year for staffing (2 part-time
    coordinators), $10,000/year for equipment and supplies.

    Staffing model: 2 paid coordinators + volunteer tutors recruited from
    the local university's education program.

    Timeline: 3 months renovation, soft launch month 4, full operation month 6.
""")


def main():
    print("=" * 60)
    print("MULTI-AGENT REVIEW: Community Learning Hub Proposal")
    print("=" * 60)
    print()

    result = parallel_review(SAMPLE_PROPOSAL)

    print()
    print("=" * 60)
    print("SYNTHESIZED ASSESSMENT")
    print("=" * 60)
    print()
    print(result)


if __name__ == "__main__":
    main()
