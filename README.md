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
*   **System Prompt**: Includes `INSTRUCTION` to guide the agent in using the planning tools.
*   **History Management**: `Planning.plan_history_processor` automatically cleans up redundant planning steps from context, keeping the history token-efficient.


## Usage

```python
from dataclasses import dataclass
from pydantic_ai import Agent
from pydantic_ai_cognitive.planning import Planning, INSTRUCTION

# Instantiate the planning toolset
planning = Planning()

agent = Agent(
    "openai:gpt-4o",
    # Add the planning instructions to the system prompt
    instructions=INSTRUCTION,
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

## Development

1.  **Install**:
    ```bash
    make install
    ```

2.  **Lint/Format**:
    ```bash
    uv run pre-commit run -a
    ```
