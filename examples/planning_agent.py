import asyncio
from dataclasses import dataclass

import history_viewer  # type: ignore[import-not-found]
from pydantic_ai import Agent

from pydantic_ai_cognitive.planning import HISTORY_PROCESSOR, INSTRUCTION, TOOLSET


@dataclass
class AgentDeps:
    pass


def add(a: int, b: int) -> int:
    return a + b


def mul(a: int, b: int) -> int:
    return a * b


agent = Agent(
    "google-gla:gemini-flash-lite-latest",
    instructions=INSTRUCTION,
    toolsets=[TOOLSET],
    tools=[add, mul],
    deps_type=AgentDeps,
    history_processors=[HISTORY_PROCESSOR, history_viewer.dump_history],
)


async def main():
    prompt = "Calculate (3 + 5) * 12 + 4 using the tools provided. Create a plan first."

    print(f"User: {prompt}")
    result = await agent.run(prompt, deps=AgentDeps())
    print(f"Agent: {result.output}")


if __name__ == "__main__":
    asyncio.run(main())
