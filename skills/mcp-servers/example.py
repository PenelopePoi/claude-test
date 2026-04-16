"""
MCP Server - Working Example

A community resource directory server that helps people find local
services — food banks, free clinics, tutoring, legal aid, shelters.

Demonstrates: tools, resources, prompts, and the FastMCP decorator API.

Requires: pip install "mcp[cli]"

Usage:
    # Run directly (stdio transport for Claude Desktop/Code)
    python example.py

    # Connect to Claude Code
    claude mcp add community-resources -- python example.py
"""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "community_resources",
    instructions=(
        "This server provides access to a community resource directory. "
        "Use it to help people find local services like food banks, clinics, "
        "tutoring, legal aid, and shelters. Search by category, zip code, "
        "or specific needs like language or accessibility."
    ),
)


# ---------------------------------------------------------------------------
# Mock data (replace with a real database or API)
# ---------------------------------------------------------------------------

RESOURCES_DB = [
    {
        "id": "res-001",
        "name": "Riverside Food Bank",
        "category": "food",
        "address": "415 River St, Portland, OR 97201",
        "zipcode": "97201",
        "hours": "Mon-Fri 9am-5pm, Sat 10am-2pm",
        "phone": "(503) 555-0101",
        "languages": ["English", "Spanish", "Vietnamese"],
        "accessibility": "Wheelchair accessible, delivery available for homebound residents",
        "description": (
            "Free groceries for anyone in need. No ID or proof of income "
            "required. Fresh produce available Wednesdays and Saturdays."
        ),
    },
    {
        "id": "res-002",
        "name": "Open Door Free Clinic",
        "category": "health",
        "address": "820 SE Morrison St, Portland, OR 97214",
        "zipcode": "97214",
        "hours": "Mon-Thu 8am-6pm, Fri 8am-12pm",
        "phone": "(503) 555-0202",
        "languages": ["English", "Spanish", "Mandarin", "ASL"],
        "accessibility": "Wheelchair accessible, ASL interpreters on staff",
        "description": (
            "Free medical care for uninsured and underinsured adults. "
            "Services include primary care, dental, vision, and mental health. "
            "Walk-ins welcome, appointments preferred."
        ),
    },
    {
        "id": "res-003",
        "name": "Homework Help Hub",
        "category": "education",
        "address": "Multnomah County Library, 801 SW 10th Ave, Portland, OR 97205",
        "zipcode": "97205",
        "hours": "Mon-Thu 3pm-7pm during school year",
        "phone": "(503) 555-0303",
        "languages": ["English", "Spanish"],
        "accessibility": "Wheelchair accessible, adaptive technology available",
        "description": (
            "Free drop-in tutoring for K-12 students in all subjects. "
            "Volunteer tutors from Portland State University. Loaner "
            "laptops and free wifi available."
        ),
    },
    {
        "id": "res-004",
        "name": "Legal Aid Services of Oregon",
        "category": "legal",
        "address": "520 SW Yamhill St, Portland, OR 97204",
        "zipcode": "97204",
        "hours": "Mon-Fri 9am-5pm",
        "phone": "(503) 555-0404",
        "languages": ["English", "Spanish", "Russian", "Somali"],
        "accessibility": "Wheelchair accessible, phone consultations available",
        "description": (
            "Free legal help for low-income Oregonians. Housing, family law, "
            "immigration, public benefits, and consumer protection. "
            "Income eligibility required for ongoing representation."
        ),
    },
    {
        "id": "res-005",
        "name": "Warm Springs Shelter",
        "category": "shelter",
        "address": "1234 NW Glisan St, Portland, OR 97209",
        "zipcode": "97209",
        "hours": "Open 24/7, intake 5pm-9pm",
        "phone": "(503) 555-0505",
        "languages": ["English", "Spanish"],
        "accessibility": "Ground floor accessible, service animals welcome",
        "description": (
            "Emergency overnight shelter for adults. 60 beds, first come "
            "first served. Includes dinner and breakfast, shower facilities, "
            "and connections to permanent housing programs."
        ),
    },
]


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

class SearchQuery(BaseModel):
    """Search parameters for finding community resources."""
    category: str | None = None
    zipcode: str | None = None
    language: str | None = None
    keyword: str | None = None


@mcp.tool()
def search_resources(query: SearchQuery) -> str:
    """Search the community resource directory by category, location, language,
    or keyword. Categories include: food, health, education, legal, shelter.
    Returns matching resources with contact info and hours."""
    import json

    matches = RESOURCES_DB

    if query.category:
        matches = [r for r in matches if r["category"] == query.category.lower()]

    if query.zipcode:
        matches = [r for r in matches if r["zipcode"] == query.zipcode]

    if query.language:
        matches = [
            r for r in matches
            if any(query.language.lower() in lang.lower() for lang in r["languages"])
        ]

    if query.keyword:
        kw = query.keyword.lower()
        matches = [
            r for r in matches
            if kw in r["name"].lower() or kw in r["description"].lower()
        ]

    if not matches:
        return json.dumps({
            "results": [],
            "message": "No resources found matching your criteria. Try broadening your search.",
        })

    # Return summary for each match
    results = [
        {
            "id": r["id"],
            "name": r["name"],
            "category": r["category"],
            "address": r["address"],
            "phone": r["phone"],
            "hours": r["hours"],
            "languages": r["languages"],
        }
        for r in matches
    ]
    return json.dumps({"results": results, "total": len(results)}, indent=2)


@mcp.tool()
def get_resource_details(resource_id: str) -> str:
    """Get full details for a specific resource, including accessibility
    information, languages supported, and complete description."""
    import json

    for r in RESOURCES_DB:
        if r["id"] == resource_id:
            return json.dumps(r, indent=2)
    return json.dumps({"error": f"Resource '{resource_id}' not found"})


@mcp.tool()
def check_accessibility(resource_id: str, needs: str) -> str:
    """Check if a specific resource meets particular accessibility needs.
    Describe the needs in plain language (e.g., 'wheelchair access',
    'ASL interpreter', 'Spanish speaking staff')."""
    import json

    for r in RESOURCES_DB:
        if r["id"] == resource_id:
            return json.dumps({
                "resource": r["name"],
                "accessibility_info": r["accessibility"],
                "languages": r["languages"],
                "your_needs": needs,
                "note": (
                    "Call ahead to confirm specific accommodations. "
                    "Staff can arrange additional support with advance notice."
                ),
            }, indent=2)
    return json.dumps({"error": f"Resource '{resource_id}' not found"})


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@mcp.resource("directory://categories")
def list_categories() -> str:
    """List all available resource categories."""
    import json
    categories = sorted(set(r["category"] for r in RESOURCES_DB))
    return json.dumps({"categories": categories})


@mcp.resource("directory://all")
def all_resources() -> str:
    """Complete directory listing."""
    import json
    return json.dumps([
        {"id": r["id"], "name": r["name"], "category": r["category"]}
        for r in RESOURCES_DB
    ], indent=2)


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

@mcp.prompt(
    name="help_find_resources",
    description="Help someone find community resources based on their situation"
)
def find_resources_prompt(situation: str, location: str) -> str:
    return (
        f"Someone needs help. Here's their situation: {situation}\n"
        f"They're located near: {location}\n\n"
        f"Search the community resource directory to find relevant services. "
        f"For each result, explain what it offers and how to access it. "
        f"Always mention accessibility options, languages available, and hours. "
        f"If they might qualify for multiple types of help, mention all of them."
    )


@mcp.prompt(
    name="accessibility_guide",
    description="Create an accessibility guide for visiting a resource"
)
def accessibility_prompt(resource_id: str, needs: str) -> str:
    return (
        f"Look up resource {resource_id} and check its accessibility info. "
        f"The person has these needs: {needs}\n\n"
        f"Create a simple, step-by-step guide for visiting this resource, "
        f"including: how to get there by transit, what to expect on arrival, "
        f"what to bring, and who to ask for help."
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
