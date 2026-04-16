"""
Prompt Caching - Working Example

A document Q&A assistant that caches a long reference document so users
can ask multiple questions without re-processing it each time.

Demonstrates: cache breakpoints, cache performance tracking, multi-turn
caching, and document-based Q&A.

Requires: pip install anthropic

Usage:
    export ANTHROPIC_API_KEY="sk-ant-..."
    python example.py
"""

import anthropic


client = anthropic.Anthropic()

# ---------------------------------------------------------------------------
# Reference document (in production, load from file or database)
# ---------------------------------------------------------------------------

REFERENCE_DOCUMENT = """
Community Health Center Accessibility Policy
Version 3.2 — Effective January 2026

1. PHYSICAL ACCESSIBILITY

1.1 All facilities must comply with ADA Title III requirements at minimum.
1.2 Entrances must have automatic doors or push-button openers.
1.3 Exam rooms must accommodate wheelchairs, scooters, and stretchers.
1.4 Height-adjustable exam tables must be available in at least 50% of rooms.
1.5 Accessible parking must be within 100 feet of the main entrance.
1.6 Wayfinding signage must include Braille and high-contrast text.

2. COMMUNICATION ACCESSIBILITY

2.1 ASL interpreters must be available within 2 hours of request, and
    within 30 minutes for emergency visits.
2.2 Written materials must be available in the top 5 languages spoken in
    the service area, determined by annual census review.
2.3 Plain-language summaries (6th grade reading level) must accompany
    all patient-facing documents.
2.4 Video remote interpreting (VRI) must be available for all languages
    24/7 via tablet devices in every exam room.
2.5 TTY/TDD lines must be maintained and tested monthly.

3. DIGITAL ACCESSIBILITY

3.1 Patient portal must meet WCAG 2.2 AA standards.
3.2 Telehealth platform must support screen readers and keyboard navigation.
3.3 Appointment scheduling must be available via phone, web, and SMS.
3.4 Patient forms must be completable electronically with assistive technology.
3.5 Digital kiosks in waiting areas must have accessibility mode with
    large text, audio guidance, and adjustable height.

4. FINANCIAL ACCESSIBILITY

4.1 Sliding scale fees based on Federal Poverty Level (FPL):
    - Below 100% FPL: No charge
    - 100-150% FPL: 25% of standard fee
    - 150-200% FPL: 50% of standard fee
    - Above 200% FPL: Standard fee with payment plans available
4.2 No patient may be denied care due to inability to pay.
4.3 Financial counselors must be available to help patients navigate
    insurance enrollment, Medicaid, and charity care programs.
4.4 Billing statements must be in plain language with clear due dates
    and payment options.

5. TRANSPORTATION

5.1 Free shuttle service within 10-mile radius for patients without
    reliable transportation.
5.2 Bus passes provided for patients using public transit to appointments.
5.3 Telehealth offered as alternative for all non-emergency visits.
5.4 Home visits available for homebound patients.

6. CULTURAL RESPONSIVENESS

6.1 Staff must complete annual cultural competency training (minimum 8 hours).
6.2 Patient intake forms must allow self-identification of cultural
    preferences, dietary needs, and traditional healing practices.
6.3 Chapel/meditation space must be available and non-denominational.
6.4 Dietary accommodations must be available for inpatient meals
    (halal, kosher, vegetarian, allergen-free).

7. MENTAL HEALTH ACCESSIBILITY

7.1 Same-day crisis appointments must be available.
7.2 Behavioral health screening integrated into all primary care visits.
7.3 Support groups offered in multiple languages.
7.4 Peer support specialists on staff.
7.5 Warm handoffs (personal introductions) required when referring
    patients between providers.

8. COMPLAINT AND FEEDBACK

8.1 Accessibility complaints must be acknowledged within 24 hours
    and resolved within 30 days.
8.2 Anonymous feedback mechanisms must be available in multiple formats
    (paper, digital, phone hotline).
8.3 Quarterly accessibility audits conducted by external evaluators
    including people with disabilities.
8.4 Annual community listening sessions open to all patients.

This policy is reviewed annually. Suggested improvements may be submitted
to the Accessibility Committee at accessibility@communityhealthcenter.org.
"""

SYSTEM_PROMPT = (
    "You are an accessibility policy expert helping community health center "
    "staff understand and implement their accessibility requirements. Answer "
    "questions based on the policy document provided. Be specific — cite "
    "section numbers. If the policy doesn't address something, say so and "
    "suggest where to look."
)


# ---------------------------------------------------------------------------
# Cache-aware Q&A function
# ---------------------------------------------------------------------------

def ask_about_document(
    question: str,
    conversation_history: list | None = None,
) -> tuple[str, dict]:
    """Ask a question about the reference document.

    Returns (answer, cache_stats) where cache_stats shows token usage.
    """
    messages = []

    # Build message with cached document + conversation history
    user_content = [
        {
            "type": "text",
            "text": f"Reference document:\n\n{REFERENCE_DOCUMENT}",
            "cache_control": {"type": "ephemeral"},
        },
    ]

    # Add conversation history if this is a follow-up
    if conversation_history:
        history_text = "\n\n".join(
            f"{'Question' if m['role'] == 'user' else 'Answer'}: {m['content']}"
            for m in conversation_history
        )
        user_content.append({
            "type": "text",
            "text": f"\nPrevious Q&A:\n{history_text}",
            "cache_control": {"type": "ephemeral"},
        })

    user_content.append({
        "type": "text",
        "text": f"\nNew question: {question}",
    })

    messages.append({"role": "user", "content": user_content})

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=[{
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=messages,
    )

    answer = response.content[0].text

    cache_stats = {
        "cache_write": getattr(response.usage, "cache_creation_input_tokens", 0),
        "cache_read": getattr(response.usage, "cache_read_input_tokens", 0),
        "uncached": response.usage.input_tokens,
        "output": response.usage.output_tokens,
    }

    return answer, cache_stats


# ---------------------------------------------------------------------------
# Interactive session
# ---------------------------------------------------------------------------

def run_session():
    """Run a multi-turn Q&A session demonstrating cache reuse."""

    questions = [
        # First question — cache write
        "What are the requirements for ASL interpreter availability?",

        # Follow-up — cache read (document is already cached)
        "What about patients who speak languages other than English?",

        # Deeper follow-up — cache read again
        "If a patient can't afford care, what options do they have under this policy?",

        # Cross-referencing — cache read
        "How does the policy ensure homebound patients aren't left out?",
    ]

    print("=" * 60)
    print("DOCUMENT Q&A WITH PROMPT CACHING")
    print("Policy: Community Health Center Accessibility")
    print("=" * 60)

    conversation = []
    total_stats = {"cache_write": 0, "cache_read": 0, "uncached": 0, "output": 0}

    for i, question in enumerate(questions, 1):
        print(f"\n--- Question {i} ---")
        print(f"Q: {question}\n")

        answer, stats = ask_about_document(question, conversation)

        print(f"A: {answer}\n")
        print(f"  Cache: write={stats['cache_write']}, read={stats['cache_read']}, "
              f"uncached={stats['uncached']}, output={stats['output']}")

        # Track cumulative stats
        for key in total_stats:
            total_stats[key] += stats[key]

        # Add to conversation history
        conversation.append({"role": "user", "content": question})
        conversation.append({"role": "assistant", "content": answer})

    # Summary
    print("\n" + "=" * 60)
    print("CACHE PERFORMANCE SUMMARY")
    print("=" * 60)
    print(f"Total cache writes: {total_stats['cache_write']} tokens")
    print(f"Total cache reads:  {total_stats['cache_read']} tokens")
    print(f"Total uncached:     {total_stats['uncached']} tokens")
    print(f"Total output:       {total_stats['output']} tokens")

    if total_stats["cache_read"] > 0:
        total_input = total_stats["cache_write"] + total_stats["cache_read"] + total_stats["uncached"]
        cache_pct = (total_stats["cache_read"] / total_input * 100) if total_input > 0 else 0
        print(f"\nCache hit rate: {cache_pct:.1f}% of input tokens served from cache")
        print("Each cached read costs 90% less than processing from scratch.")


if __name__ == "__main__":
    run_session()
