# pydantic-ai-cognitive

[![Release](https://img.shields.io/github/v/release/cradiator/pydantic-ai-cognitive)](https://img.shields.io/github/v/release/cradiator/pydantic-ai-cognitive)
[![Build status](https://img.shields.io/github/actions/workflow/status/cradiator/pydantic-ai-cognitive/main.yml?branch=main)](https://github.com/cradiator/pydantic-ai-cognitive/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/cradiator/pydantic-ai-cognitive/branch/main/graph/badge.svg)](https://codecov.io/gh/cradiator/pydantic-ai-cognitive)
[![Commit activity](https://img.shields.io/github/commit-activity/m/cradiator/pydantic-ai-cognitive)](https://img.shields.io/github/commit-activity/m/cradiator/pydantic-ai-cognitive)
[![License](https://img.shields.io/github/license/cradiator/pydantic-ai-cognitive)](https://img.shields.io/github/license/cradiator/pydantic-ai-cognitive)

Cognitive toolsets for [pydantic-ai](https://github.com/pydantic/pydantic-ai).

## Features

### Planning

The `planning` module enables agents to create, track, and execute step-by-step plans.

*   **Planning Class**: `Planning` encapuslates the state of the plan.
*   **Toolset**: `Planning.toolset()` returns a toolset with bound methods: `plan_create`, `plan_mark_step_complete`, `plan_show_progress`.
*   **Self-Contained Instructions**: `plan_create` includes system instructions to guide the agent in using the planning tools effectively.
*   **History Management**: `Planning.plan_history_processor` automatically cleans up redundant planning steps from context, keeping the history token-efficient.

### Skills

The `skills` module allows you to organize and dynamically load skill documentation that AI agents can reference.

*   **Skills Class**: `Skills` manages a collection of skills stored as markdown files with YAML frontmatter.
*   **Recursive Registration**: Register all skills from a folder with a single call, supporting nested directory structures.
*   **Dynamic Toolset**: `Skills.toolset()` creates a tool that provides comprehensive instructions to AI agents on how to load and use skills.
*   **Artifact Support**: Load skill.md files or additional artifacts (examples, cheatsheets, etc.) referenced within skills.


## Usage

### Planning Example

```python
from pydantic_ai import Agent
from pydantic_ai_cognitive.planning import Planning

# Instantiate the planning toolset
planning = Planning()

agent = Agent(
    "openai:gpt-4o",
    # Register the planning toolset
    toolsets=[planning.toolset()],
    # Register the history processor to keep the context clean
    history_processors=[planning.plan_history_processor],
)

result = agent.run_sync(
    "Create a plan to write a short poem about Python, then write it.",
)
print(result.output)
```

### Skills Example

First, create a skill with YAML frontmatter:

```markdown
<!-- python_practices/skill.md -->
---
name: python-best-practices
description: Guidance on Python coding best practices
license: CC-BY-4.0
---

# Python Best Practices

## Key Principles
1. Write readable code
2. Follow PEP 8
3. Use type hints
4. Write tests
```

Then use it with an agent:

```python
from pydantic_ai import Agent
from pydantic_ai_cognitive import Skills

# Register skills from a folder
skills = Skills()
skills.register_skill("./my_skills")  # Recursively finds all skill.md files

agent = Agent(
    "openai:gpt-4o",
    # Register the skills toolset
    toolsets=[skills.toolset()],
)

result = agent.run_sync(
    "What are Python best practices for writing functions?",
)
print(result.output)
# The agent will automatically load the python-best-practices skill to answer
```

## Documentation

- **[Planning](docs/PLANNING.md)**: Detailed planning module documentation
- **[Skills](docs/SKILLS.md)**: Detailed skills module documentation

## Examples

See the [examples/](examples/) directory for complete working examples:
- [planning_agent.py](examples/planning_agent.py): Planning system demonstration
- [skills_example.py](examples/skills_example.py): Skills system demonstration

## Development

1.  **Install**:
    ```bash
    make install
    ```

2.  **Lint/Format**:
    ```bash
    uv run pre-commit run -a
    ```
