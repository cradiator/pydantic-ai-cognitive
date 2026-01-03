import asyncio

import history_viewer  # type: ignore[import-not-found]
from pydantic_ai import Agent

from pydantic_ai_cognitive.planning import Planning


def add(a: int, b: int) -> int:
    return a + b


def mul(a: int, b: int) -> int:
    return a * b


planning = Planning()

agent = Agent(
    "google-gla:gemini-flash-lite-latest",
    toolsets=[planning.toolset()],
    tools=[add, mul],
    history_processors=[planning.plan_history_processor, history_viewer.dump_history],
)


async def main():
    prompt = "Calculate (3 + 5) * 12 + 4 using the tools provided. Create a plan first."

    print(f"User: {prompt}")
    result = await agent.run(prompt)
    print(f"Agent: {result.output}")


if __name__ == "__main__":
    asyncio.run(main())
