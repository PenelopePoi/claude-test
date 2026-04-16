# Skill Library

A living, self-improving knowledge base of reusable skills for building with the Claude API.

## Skills

| Skill | Description |
|---|---|
| [computer-use-tool](skills/computer-use-tool/) | Let Claude see and control a desktop via screenshots and actions |
| [tool-use](skills/tool-use/) | Give Claude the ability to call functions in your application |
| [multi-agent-orchestration](skills/multi-agent-orchestration/) | Coordinate multiple Claude instances to tackle complex problems |
| [mcp-servers](skills/mcp-servers/) | Build servers that extend what Claude can do via Model Context Protocol |

## Contributing a New Skill

1. Create a directory under `skills/<skill-name>/`
2. Add a `README.md` with: overview, setup, usage, best practices, changelog
3. Add working example code (`example.py` or similar)
4. Update this table

See [CLAUDE.md](CLAUDE.md) for full conventions.
