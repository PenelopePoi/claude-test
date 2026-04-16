"""
Computer Use Tool - Working Example

A complete agentic loop that lets Claude control a desktop environment.
Requires: pip install anthropic

Usage:
    export ANTHROPIC_API_KEY="sk-ant-..."
    python example.py

You must implement capture_screenshot() and the action handlers
for your specific environment (VM, Docker, local display, etc.).
"""

import anthropic
import base64
import math
import subprocess
import time


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MODEL = "claude-opus-4-6"
BETA_HEADER = "computer-use-2025-11-24"
TOOL_VERSION = "computer_20251124"
DISPLAY_WIDTH = 1024
DISPLAY_HEIGHT = 768
MAX_ITERATIONS = 15

TOOLS = [
    {
        "type": TOOL_VERSION,
        "name": "computer",
        "display_width_px": DISPLAY_WIDTH,
        "display_height_px": DISPLAY_HEIGHT,
    },
    {
        "type": "bash_20250124",
        "name": "bash",
    },
    {
        "type": "text_editor_20250728",
        "name": "str_replace_based_edit_tool",
    },
]

SYSTEM_PROMPT = """You are a computer use agent that helps people accomplish
meaningful tasks on their computer. After each action, take a screenshot to
verify the result before proceeding. If something didn't work as expected,
try an alternative approach. Use keyboard shortcuts when UI elements are
hard to click precisely. Prioritize accessibility and clarity in every step."""


# ---------------------------------------------------------------------------
# Screenshot capture (implement for your environment)
# ---------------------------------------------------------------------------

def capture_screenshot() -> str:
    """Capture a screenshot and return it as a base64-encoded PNG string.

    Example implementations:
      - Linux/Xvfb:  subprocess + xwd + convert
      - pyautogui:   pyautogui.screenshot()
      - macOS:       screencapture command
    """
    # Uncomment one of these or write your own:

    # --- pyautogui (cross-platform) ---
    # import pyautogui, io
    # img = pyautogui.screenshot()
    # buf = io.BytesIO()
    # img.save(buf, format="PNG")
    # return base64.standard_b64encode(buf.getvalue()).decode("utf-8")

    # --- Linux with scrot ---
    # result = subprocess.run(
    #     ["scrot", "-o", "/tmp/screenshot.png"],
    #     capture_output=True,
    # )
    # with open("/tmp/screenshot.png", "rb") as f:
    #     return base64.standard_b64encode(f.read()).decode("utf-8")

    raise NotImplementedError(
        "Implement capture_screenshot() for your environment. "
        "See comments above for examples."
    )


# ---------------------------------------------------------------------------
# Action execution (implement for your environment)
# ---------------------------------------------------------------------------

def execute_action(tool_input: dict) -> list:
    """Execute a computer action and return the tool result content blocks.

    Returns a list of content blocks. For screenshot actions, returns an
    image block. For other actions, returns a text block.
    """
    action = tool_input.get("action")

    if action == "screenshot":
        screenshot_b64 = capture_screenshot()
        return [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": screenshot_b64,
                },
            }
        ]

    if action == "left_click":
        x, y = tool_input["coordinate"]
        _click(x, y, button="left")
        return [{"type": "text", "text": f"Clicked at ({x}, {y})"}]

    if action == "right_click":
        x, y = tool_input["coordinate"]
        _click(x, y, button="right")
        return [{"type": "text", "text": f"Right-clicked at ({x}, {y})"}]

    if action == "double_click":
        x, y = tool_input["coordinate"]
        _click(x, y, button="left", clicks=2)
        return [{"type": "text", "text": f"Double-clicked at ({x}, {y})"}]

    if action == "triple_click":
        x, y = tool_input["coordinate"]
        _click(x, y, button="left", clicks=3)
        return [{"type": "text", "text": f"Triple-clicked at ({x}, {y})"}]

    if action == "middle_click":
        x, y = tool_input["coordinate"]
        _click(x, y, button="middle")
        return [{"type": "text", "text": f"Middle-clicked at ({x}, {y})"}]

    if action == "mouse_move":
        x, y = tool_input["coordinate"]
        _move_mouse(x, y)
        return [{"type": "text", "text": f"Moved mouse to ({x}, {y})"}]

    if action == "left_click_drag":
        sx, sy = tool_input["startCoordinate"]
        ex, ey = tool_input["endCoordinate"]
        _drag(sx, sy, ex, ey)
        return [{"type": "text", "text": f"Dragged ({sx},{sy}) -> ({ex},{ey})"}]

    if action == "type":
        text = tool_input["text"]
        _type_text(text)
        return [{"type": "text", "text": f"Typed: {text[:50]}..."}]

    if action == "key":
        key = tool_input["key"]
        _press_key(key)
        return [{"type": "text", "text": f"Pressed: {key}"}]

    if action == "scroll":
        x, y = tool_input["coordinate"]
        direction = tool_input["scroll_direction"]
        amount = tool_input["scroll_amount"]
        _scroll(x, y, direction, amount)
        return [{"type": "text", "text": f"Scrolled {direction} by {amount}"}]

    if action == "wait":
        duration = tool_input.get("duration", 1)
        time.sleep(duration)
        return [{"type": "text", "text": f"Waited {duration}s"}]

    return [{"type": "text", "text": f"Unknown action: {action}"}]


# ---------------------------------------------------------------------------
# Low-level action helpers (implement for your environment)
# ---------------------------------------------------------------------------
# These are stubs. Replace with xdotool, pyautogui, or your tool of choice.

def _click(x: int, y: int, button: str = "left", clicks: int = 1):
    """Click at screen coordinates."""
    # xdotool example:
    # subprocess.run(["xdotool", "mousemove", str(x), str(y)])
    # subprocess.run(["xdotool", "click", "--repeat", str(clicks), "1"])
    pass


def _move_mouse(x: int, y: int):
    # subprocess.run(["xdotool", "mousemove", str(x), str(y)])
    pass


def _drag(sx: int, sy: int, ex: int, ey: int):
    # subprocess.run(["xdotool", "mousemove", str(sx), str(sy)])
    # subprocess.run(["xdotool", "mousedown", "1"])
    # subprocess.run(["xdotool", "mousemove", str(ex), str(ey)])
    # subprocess.run(["xdotool", "mouseup", "1"])
    pass


def _type_text(text: str):
    # subprocess.run(["xdotool", "type", "--", text])
    pass


def _press_key(key: str):
    # Map Claude's key format to xdotool format, e.g. "ctrl+s" -> "ctrl+s"
    # subprocess.run(["xdotool", "key", key])
    pass


def _scroll(x: int, y: int, direction: str, amount: int):
    # button = {"up": "4", "down": "5", "left": "6", "right": "7"}[direction]
    # subprocess.run(["xdotool", "mousemove", str(x), str(y)])
    # for _ in range(amount):
    #     subprocess.run(["xdotool", "click", button])
    pass


# ---------------------------------------------------------------------------
# Coordinate scaling (for high-resolution displays)
# ---------------------------------------------------------------------------

def get_scale_factor(actual_width: int, actual_height: int) -> float:
    """Calculate the scale factor for high-res displays.

    The API constrains images to ~1568px max edge. If your display is larger,
    resize screenshots by this factor before sending, and divide Claude's
    coordinates by this factor before executing clicks.
    """
    long_edge = max(actual_width, actual_height)
    total_pixels = actual_width * actual_height
    long_edge_scale = 1568 / long_edge
    total_pixels_scale = math.sqrt(1_150_000 / total_pixels)
    return min(1.0, long_edge_scale, total_pixels_scale)


# ---------------------------------------------------------------------------
# Main agentic loop
# ---------------------------------------------------------------------------

def run(task: str) -> None:
    """Run the computer use agent loop for a given task."""
    client = anthropic.Anthropic()

    messages = [{"role": "user", "content": task}]

    print(f"Task: {task}")
    print(f"Model: {MODEL} | Max iterations: {MAX_ITERATIONS}")
    print("-" * 60)

    for i in range(1, MAX_ITERATIONS + 1):
        print(f"\n[Iteration {i}]")

        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
            betas=[BETA_HEADER],
        )

        # Add assistant response to history
        messages.append({"role": "assistant", "content": response.content})

        # Process each content block
        tool_results = []
        for block in response.content:
            if block.type == "text":
                print(f"  Claude: {block.text}")

            elif block.type == "tool_use":
                print(f"  Tool: {block.name} -> {block.input.get('action', block.input.get('command', '?'))}")

                if block.name == "computer":
                    result_content = execute_action(block.input)
                elif block.name == "bash":
                    # Execute bash command and return output
                    proc = subprocess.run(
                        block.input.get("command", "echo 'no command'"),
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    output = proc.stdout + proc.stderr
                    result_content = output if output else "(no output)"
                else:
                    result_content = f"Tool '{block.name}' not implemented"

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_content,
                })

        # No tool calls = task complete
        if not tool_results:
            print("\nDone - Claude finished the task.")
            return

        messages.append({"role": "user", "content": tool_results})

    print(f"\nStopped after {MAX_ITERATIONS} iterations (safety limit).")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

EXAMPLE_TASKS = [
    # Accessibility - help someone navigate a UI they can't easily use
    "Open the system accessibility settings and enable high-contrast mode.",

    # Learning - help a student research a topic
    "Open the browser, search for 'how coral reefs support marine biodiversity', "
    "and save the first three results as bookmarks.",

    # Creative expression - help someone share their voice
    "Open a text editor and write a short letter template for someone "
    "reconnecting with a friend they've lost touch with.",

    # Community - help organize people around something that matters
    "Open the calendar app and create a recurring weekly event called "
    "'Neighborhood Cleanup' on Saturday mornings at 9 AM.",

    # Health - help someone take care of themselves
    "Open the browser and find a beginner-friendly guided meditation video.",
]

if __name__ == "__main__":
    # Default: help someone make their computer more accessible
    run(EXAMPLE_TASKS[0])
