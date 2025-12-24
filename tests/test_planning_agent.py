from __future__ import annotations

from dataclasses import dataclass

import pytest
from pydantic_ai import Agent, ModelMessage, ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from pydantic_ai_cognitive.planning import Planning
from pydantic_ai_cognitive.utils import EnumerateMessageWithParts

pytestmark = pytest.mark.anyio


@dataclass
class AgentDeps:
    pass


def test_planning_agent_flow() -> None:
    """
    Test the planning agent flow using FunctionModel to simulate the model's behavior.
    This test verifies:
    1. The model calls plan_create.
    2. The model calls plan_show_progress.
    3. The model calls plan_mark_step_complete.
    4. The model calls plan_show_progress again.
    5. The history processor correctly manages the history (tested via inspecting messages passed to the model).
    """

    # We track call count to simulate different responses
    call_count = 0

    def model_function(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        nonlocal call_count
        call_count += 1

        # 1. First call: Create a plan
        if call_count == 1:
            return ModelResponse(
                parts=[ToolCallPart("plan_create", {"steps": ["Step 1", "Step 2"]}, tool_call_id="call_1")]
            )

        # 2. Second call: Show progress (after plan created)
        elif call_count == 2:
            # Verify we received the tool return for plan_create
            last_msg = messages[-1]
            assert isinstance(last_msg.parts[0], ToolReturnPart)
            assert last_msg.parts[0].tool_name == "plan_create"

            content = last_msg.parts[0].content
            assert "Current Plan:" in content
            assert "[ ] 1. Step 1" in content
            assert "[ ] 2. Step 2" in content

            return ModelResponse(parts=[ToolCallPart("plan_show_progress", {}, tool_call_id="call_2")])

        # 3. Third call: Mark step 1 complete
        elif call_count == 3:
            # Verify we received return for plan_show_progress
            last_msg = messages[-1]
            assert isinstance(last_msg.parts[0], ToolReturnPart)
            assert last_msg.parts[0].tool_name == "plan_show_progress"

            content = last_msg.parts[0].content
            assert "Current Plan:" in content
            assert "[ ] 1. Step 1" in content
            assert "[ ] 2. Step 2" in content
            return ModelResponse(parts=[ToolCallPart("plan_mark_step_complete", {"step_id": 1}, tool_call_id="call_3")])

        # 4. Fourth call: Show progress again
        elif call_count == 4:
            # Verify return for mark complete
            last_msg = messages[-1]
            assert isinstance(last_msg.parts[0], ToolReturnPart)
            assert last_msg.parts[0].tool_name == "plan_mark_step_complete"
            assert "[x] 1" in last_msg.parts[0].content

            return ModelResponse(parts=[ToolCallPart("plan_show_progress", {}, tool_call_id="call_4")])

        # 5. Fifth call: Finish
        elif call_count == 5:
            # Verify return for second show progress
            tool_calls_in_history: list[ToolCallPart] = []
            for _, parts in EnumerateMessageWithParts(messages):
                for part in parts:
                    if isinstance(part, ToolCallPart):
                        tool_calls_in_history.append(part)

            has_call_2 = any(p.tool_call_id == "call_2" for p in tool_calls_in_history)
            has_call_4 = any(p.tool_call_id == "call_4" for p in tool_calls_in_history)
            assert has_call_4, "History should contain the latest show_progress call"
            assert not has_call_2, "History should NOT contain the older show_progress call"

            return ModelResponse(parts=[TextPart("All done")])

        return ModelResponse(parts=[TextPart("Unexpected call")])

    planning = Planning()

    agent: Agent[AgentDeps, str] = Agent(
        model=FunctionModel(model_function),
        toolsets=[planning.toolset()],
        history_processors=[planning.plan_history_processor],
        deps_type=AgentDeps,
        output_type=str,
    )
    deps = AgentDeps()
    result = agent.run_sync("Please do the task", deps=deps)

    assert result.output == "All done"
    assert call_count == 5
