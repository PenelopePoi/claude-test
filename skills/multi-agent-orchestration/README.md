# Multi-Agent Orchestration

Coordinate multiple Claude instances to tackle problems too large or
too varied for a single conversation — the way a team of people would.

## What It Is

Multi-agent orchestration means running several Claude conversations that
work together. An orchestrator breaks a task into pieces, delegates to
specialist agents, and synthesizes their results. This mirrors how real
teams work: a project lead coordinates specialists who each bring
different strengths.

**Why it matters:** Complex real-world problems — translating a curriculum
into multiple languages, reviewing a community health proposal from legal,
medical, and accessibility angles — benefit from focused attention on each
part rather than asking one generalist to do everything at once.

## Patterns

### 1. Orchestrator-Worker

One agent coordinates, others execute. Best for tasks with clearly
separable subtasks.

```
Orchestrator
  ├── Worker A (research)
  ├── Worker B (writing)
  └── Worker C (review)
```

### 2. Pipeline

Each agent's output feeds the next. Best for sequential transformation.

```
Translator → Editor → Accessibility Reviewer → Publisher
```

### 3. Parallel Fan-Out

Multiple agents work the same task independently, then results are
compared or merged. Best for getting diverse perspectives.

```
         ┌── Reviewer 1 ──┐
Task ────┼── Reviewer 2 ──┼──→ Synthesizer
         └── Reviewer 3 ──┘
```

## Implementation

### Basic Orchestrator-Worker

```python
import anthropic
import concurrent.futures

client = anthropic.Anthropic()


def call_agent(system_prompt: str, task: str, model: str = "claude-sonnet-4-6") -> str:
    """Run a single agent conversation and return its text response."""
    response = client.messages.create(
        model=model,
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": task}],
    )
    return "".join(
        block.text for block in response.content if hasattr(block, "text")
    )


def orchestrate(task: str) -> str:
    """Break a task into subtasks, delegate, and synthesize."""

    # Step 1: Ask the orchestrator to decompose the task
    plan = call_agent(
        system_prompt=(
            "You are a project coordinator. Break the given task into "
            "2-4 independent subtasks. Return ONLY a JSON array of strings, "
            "each describing one subtask. No other text."
        ),
        task=task,
    )

    import json
    subtasks = json.loads(plan)
    print(f"Subtasks: {subtasks}")

    # Step 2: Fan out to worker agents in parallel
    worker_prompt = (
        "You are a specialist. Complete your assigned task thoroughly. "
        "Be specific and actionable."
    )

    with concurrent.futures.ThreadPoolExecutor() as pool:
        futures = {
            pool.submit(call_agent, worker_prompt, subtask): subtask
            for subtask in subtasks
        }
        results = {}
        for future in concurrent.futures.as_completed(futures):
            subtask = futures[future]
            results[subtask] = future.result()

    # Step 3: Synthesize results
    synthesis_input = "\n\n".join(
        f"## {subtask}\n{result}" for subtask, result in results.items()
    )

    return call_agent(
        system_prompt=(
            "You are a synthesizer. Combine the following specialist "
            "contributions into one coherent, well-organized response. "
            "Preserve all important details. Resolve any contradictions "
            "by noting both perspectives."
        ),
        task=f"Original task: {task}\n\nSpecialist contributions:\n{synthesis_input}",
    )
```

### Pipeline Pattern

```python
def pipeline(text: str) -> str:
    """Process text through a sequence of specialist agents."""

    stages = [
        {
            "name": "Translator",
            "system": (
                "Translate the following text into clear, simple English "
                "accessible to someone with an 8th-grade reading level. "
                "Preserve all meaning."
            ),
        },
        {
            "name": "Cultural Reviewer",
            "system": (
                "Review this translation for cultural sensitivity. Flag "
                "anything that might not translate well across cultures "
                "and suggest alternatives. Return the improved text."
            ),
        },
        {
            "name": "Accessibility Editor",
            "system": (
                "Review this text for accessibility. Ensure it works with "
                "screen readers, uses clear structure, and avoids idioms "
                "that might confuse non-native speakers. Return the final text."
            ),
        },
    ]

    current = text
    for stage in stages:
        print(f"  [{stage['name']}]")
        current = call_agent(stage["system"], current)

    return current
```

### Parallel Review (Fan-Out)

```python
def parallel_review(proposal: str) -> str:
    """Get independent reviews from multiple perspectives, then synthesize."""

    reviewers = [
        {
            "name": "Community Impact",
            "system": (
                "Review this proposal from the perspective of community "
                "impact. Who benefits? Who might be left out? What are "
                "the long-term social effects?"
            ),
        },
        {
            "name": "Practical Feasibility",
            "system": (
                "Review this proposal for practical feasibility. What "
                "resources are needed? What could go wrong? What's the "
                "realistic timeline?"
            ),
        },
        {
            "name": "Accessibility & Inclusion",
            "system": (
                "Review this proposal for accessibility and inclusion. "
                "Does it serve people with disabilities? Different "
                "languages? Different income levels?"
            ),
        },
    ]

    # Fan out reviews in parallel
    with concurrent.futures.ThreadPoolExecutor() as pool:
        futures = {
            pool.submit(call_agent, r["system"], proposal): r["name"]
            for r in reviewers
        }
        reviews = {}
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            reviews[name] = future.result()

    # Synthesize
    review_text = "\n\n".join(
        f"### {name}\n{review}" for name, review in reviews.items()
    )

    return call_agent(
        system_prompt=(
            "Synthesize these independent reviews into a single assessment. "
            "Highlight consensus, flag disagreements, and provide an overall "
            "recommendation with specific action items."
        ),
        task=f"Proposal:\n{proposal}\n\nReviews:\n{review_text}",
    )
```

## Passing Context Between Agents

Agents don't share memory. You must explicitly pass relevant context:

```python
# Pass only what the next agent needs — not the full history
summary = call_agent(
    "Summarize the key findings in 3 bullet points.",
    long_research_output,
)

recommendation = call_agent(
    "Based on these findings, recommend next steps.",
    summary,  # Focused context, not the raw research
)
```

**Rules of thumb:**
- Summarize before passing to the next agent
- Include the original task for context
- Don't pass raw API responses — extract what matters
- Each agent should be able to do its job from its input alone

## Best Practices

- **Start simple.** A single agent with good tools often beats a multi-agent
  system. Add agents only when a task genuinely benefits from specialization.
- **Keep agents focused.** Each agent should have a clear, narrow role defined
  in its system prompt. Vague roles lead to overlapping, contradictory output.
- **Limit fan-out.** 2-4 parallel agents is the sweet spot. More than that and
  synthesis becomes the bottleneck.
- **Use cheaper models for simple subtasks.** Route research to Sonnet, synthesis
  to Opus. Not every agent needs the most capable model.
- **Set timeouts.** Use `concurrent.futures` timeouts to prevent one slow agent
  from blocking the whole pipeline.
- **Log everything.** In multi-agent systems, debugging requires seeing what each
  agent received and produced.

## When NOT to Use Multi-Agent

- The task fits in a single conversation
- You're adding agents for "architecture" rather than genuine need
- The subtasks depend heavily on each other (pipeline is fine; tangled
  dependencies are not)
- You haven't tried good tool use with a single agent first

## Changelog

- 2026-04-16: Initial version. Covers orchestrator-worker, pipeline, and
  parallel fan-out patterns with working examples.
