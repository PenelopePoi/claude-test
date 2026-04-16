# Computer Use Tool

Let Claude see and control a desktop environment through screenshots and actions -
helping people accomplish tasks they couldn't easily do alone.

## What It Is

Computer Use gives Claude eyes and hands on a screen. You send it screenshots, it
responds with actions (click, type, scroll, etc.), you execute those actions and
send a new screenshot. This loop repeats until the task is done.

```
You send screenshot -> Claude returns action -> You execute action -> Repeat
```

**Why it matters:** This enables assistive technology for people who struggle with
complex interfaces, automates tedious workflows so people can focus on what matters,
and makes computers more accessible to everyone regardless of technical skill.

## Setup

```bash
pip install anthropic
```

Set your API key:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Model & Version Matrix

| Tool Version | Beta Header | Supported Models |
|---|---|---|
| `computer_20251124` | `computer-use-2025-11-24` | Opus 4.6, Sonnet 4.6, Opus 4.5 |
| `computer_20250124` | `computer-use-2025-01-24` | Sonnet 4.5, Haiku 4.5, Opus 4, Sonnet 4 |

Use the latest version (`computer_20251124`) unless you need an older model.

## Tool Definition

```python
tools = [
    {
        "type": "computer_20251124",
        "name": "computer",
        "display_width_px": 1024,
        "display_height_px": 768,
    }
]
```

Optional parameters:
- `display_number` - X11 display number (for virtual environments)
- `enable_zoom` - Enable zoom action (`computer_20251124` only)

## The Agentic Loop

The core pattern has three parts:

1. **Call Claude** with tools and message history
2. **Execute** any tool calls Claude returns
3. **Loop** until Claude responds with no tool calls (task complete)

```python
response = client.beta.messages.create(
    model="claude-opus-4-6",
    max_tokens=4096,
    tools=tools,
    messages=messages,
    betas=["computer-use-2025-11-24"],
)
```

See `example.py` for the full working loop.

## Action Types

### Mouse Actions

| Action | Parameters | Description |
|---|---|---|
| `left_click` | `coordinate: [x, y]` | Left click |
| `right_click` | `coordinate: [x, y]` | Right click |
| `double_click` | `coordinate: [x, y]` | Double click |
| `triple_click` | `coordinate: [x, y]` | Triple click |
| `middle_click` | `coordinate: [x, y]` | Middle click |
| `mouse_move` | `coordinate: [x, y]` | Move cursor |
| `left_click_drag` | `startCoordinate, endCoordinate` | Drag |
| `left_mouse_down` | `coordinate: [x, y]` | Press and hold |
| `left_mouse_up` | `coordinate: [x, y]` | Release |

### Keyboard Actions

| Action | Parameters | Description |
|---|---|---|
| `type` | `text: "string"` | Type text |
| `key` | `key: "ctrl+s"` | Press key combo |
| `hold_key` | `key, duration` | Hold a key |

### Screen Actions

| Action | Parameters | Description |
|---|---|---|
| `screenshot` | none | Capture the display |
| `scroll` | `coordinate, scroll_direction, scroll_amount` | Scroll |
| `zoom` | `region: [x1, y1, x2, y2]` | Zoom into region (requires `enable_zoom`) |
| `wait` | `duration` | Pause execution |

### Modifier Keys

Click actions accept an optional `text` field for modifier keys (e.g. shift-click to select a range of files to share with a collaborator):
```json
{"action": "left_click", "coordinate": [500, 300], "text": "shift"}
```

## Best Practices

### Resolution
- Use **1024x768** for general tasks. It's the sweet spot for accuracy vs. detail.
- Avoid resolutions above 1920x1080 - performance degrades.
- The API constrains images to ~1568px max edge. Scale coordinates accordingly.

### Prompting
- Give **specific, step-by-step instructions** rather than vague goals.
- Add this to your system prompt for reliability:
  > After each step, take a screenshot and evaluate if you achieved the right outcome. If not, try again.
- Tell Claude to use **keyboard shortcuts** for tricky UI elements (dropdowns, sliders).

### Safety
- **Always run in an isolated environment** (VM, container, sandbox). Never your main machine.
- **Set a max iteration limit** (10-20 is typical) to prevent runaway loops.
- **Don't pass credentials** to Claude. Use pre-authenticated sessions.
- **Limit network access** with domain allowlists.
- **Require human confirmation** for destructive or financial actions.

### Coordinate Scaling

If your actual display resolution differs from what you tell Claude, scale coordinates:

```python
import math

def get_scale_factor(actual_width, actual_height):
    long_edge = max(actual_width, actual_height)
    total_pixels = actual_width * actual_height
    long_edge_scale = 1568 / long_edge
    total_pixels_scale = math.sqrt(1_150_000 / total_pixels)
    return min(1.0, long_edge_scale, total_pixels_scale)
```

## Example Use Cases

These are the kinds of tasks Computer Use is well-suited for:

- **Accessibility** - Enable high-contrast mode, increase font sizes, or configure
  screen readers for someone who needs help navigating settings.
- **Learning** - Research a topic across multiple tabs, collect sources, and
  organize them into bookmarks or notes for a student.
- **Creative expression** - Help someone draft a letter, design a flyer for a
  community event, or set up a blog to share their story.
- **Community building** - Create calendar events for neighborhood cleanups,
  fill out volunteer sign-up forms, or organize shared documents.
- **Health & wellbeing** - Find guided meditation resources, set up medication
  reminders, or navigate telehealth appointment portals.

See `example.py` for runnable versions of these.

## Companion Tools

Computer Use works well alongside these tools in the same request:

| Tool | Type | Purpose |
|---|---|---|
| Bash | `bash_20250124` | Run shell commands |
| Text Editor | `text_editor_20250728` | Edit files with str_replace |

## Reference Implementation

Anthropic's Docker-based demo with full tool implementations and web UI:
https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo

## Changelog

- 2026-04-16: Initial version. Covers `computer_20251124` and `computer_20250124`.
- 2026-04-16: Updated with meaningful example tasks and use cases. Examples now
  reflect real human needs - accessibility, learning, community, health, creative
  expression - rather than generic placeholders.
