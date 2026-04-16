# Skill Library

This repo is a living, self-improving knowledge base of reusable skills for building with the Claude API and related tools.

## Purpose

Each skill is a standalone guide with working example code. The goal is to accumulate battle-tested patterns that get better over time through usage and iteration.

## Repo Structure

```
skills/
  <skill-name>/
    README.md       # Guide: what it is, how it works, best practices
    example.py      # Working example code
    ...             # Additional files as needed
```

## Conventions

- **One skill per directory** under `skills/`.
- Every skill must have a `README.md` with: overview, setup, usage, API reference, best practices.
- Every skill should have working example code that can be run standalone.
- Keep guides concise and opinionated - link to official docs for exhaustive reference.
- When updating a skill, note what changed and why at the bottom of its README under a `## Changelog` section.
- Use Python as the default language unless the skill is language-specific.

## How to Improve

When revisiting a skill:
1. Check if the API version or model list has changed.
2. Verify code examples still work.
3. Add lessons learned from real usage.
4. Remove outdated information.
