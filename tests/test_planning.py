from datetime import datetime

from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    RequestUsage,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)

from pydantic_ai_cognitive.planning import Planning


def test_plan_create():
    planning = Planning()
    steps = ["Step 1", "Step 2"]
    result = planning.plan_create(steps)
    assert "1. Step 1" in result
    assert "2. Step 2" in result
    assert "[ ] 1" in result

    assert len(planning.steps) == 2


def test_plan_mark_step_complete() -> None:
    planning = Planning()
    planning.plan_create(["Do X", "Do Y"])

    result = planning.plan_mark_step_complete(1)
    assert "[x] 1" in result
    assert "[ ] 2" in result

    result = planning.plan_mark_step_complete(2)
    assert "[x] 2" in result

    result = planning.plan_mark_step_complete(99)
    assert "Step 99 not found" in result


def test_plan_show_progress() -> None:
    planning = Planning()
    planning.plan_create(["A", "B"])
    result = planning.plan_show_progress()
    assert "Current Plan:" in result
    assert "[ ] 1. A" in result
    assert "[ ] 2. B" in result


def test_toolset_instructions() -> None:
    """Verify that the planning instructions are included in the tool description."""
    planning = Planning()
    tools = planning.toolset().tools
    plan_create_tool = tools["plan_create"]

    assert plan_create_tool is not None
    assert plan_create_tool.description is not None
    assert "Planning System Instructions" in plan_create_tool.description
    assert "you MUST call 'plan_create'" in plan_create_tool.description


def test_plan_history_processor() -> None:
    planning = Planning()
    # Setup some timestamps
    ts = datetime.now()

    # Create a history with redundant calls
    # Sequence:
    # 1. plan_create (old)
    # 2. plan_create (new - keep)
    # 3. plan_mark_step_complete (step 1) -> (old)
    # 4. plan_show_progress (old)
    # 5. plan_mark_step_complete (step 2) -> (new - keep)
    # 6. plan_show_progress (new - keep)
    # Also include some user/text parts that should remain

    history: list[ModelRequest | ModelResponse] = [
        # Message 0: User prompt
        ModelRequest(parts=[UserPromptPart(content="Start")], kind="request", timestamp=ts),
        # Message 1: plan_create (OLD) - Call
        ModelResponse(
            parts=[ToolCallPart(tool_name="plan_create", args={"steps": ["A", "B"]}, tool_call_id="id_create_1")],
            kind="response",
            timestamp=ts,
            usage=RequestUsage(),
        ),
        # Message 2: plan_create (OLD) - Return
        ModelRequest(
            parts=[ToolReturnPart(tool_name="plan_create", content="Plan created", tool_call_id="id_create_1")],
            kind="request",
            timestamp=ts,
        ),
        # Message 3: plan_create (NEW) - Call
        ModelResponse(
            parts=[ToolCallPart(tool_name="plan_create", args={"steps": ["A", "B", "C"]}, tool_call_id="id_create_2")],
            kind="response",
            timestamp=ts,
            usage=RequestUsage(),
        ),
        # Message 4: plan_create (NEW) - Return
        ModelRequest(
            parts=[ToolReturnPart(tool_name="plan_create", content="Plan created 2", tool_call_id="id_create_2")],
            kind="request",
            timestamp=ts,
        ),
        # Message 5: plan_mark_step_complete (OLD) - Call
        ModelResponse(
            parts=[ToolCallPart(tool_name="plan_mark_step_complete", args={"step_id": 1}, tool_call_id="id_mark_1")],
            kind="response",
            timestamp=ts,
            usage=RequestUsage(),
        ),
        # Message 6: plan_mark_step_complete (OLD) - Return
        ModelRequest(
            parts=[
                ToolReturnPart(tool_name="plan_mark_step_complete", content="Step 1 done", tool_call_id="id_mark_1")
            ],
            kind="request",
            timestamp=ts,
        ),
        # Message 7: plan_show_progress (OLD) - Call
        ModelResponse(
            parts=[ToolCallPart(tool_name="plan_show_progress", args={}, tool_call_id="id_show_1")],
            kind="response",
            timestamp=ts,
            usage=RequestUsage(),
        ),
        # Message 8: plan_show_progress (OLD) - Return
        ModelRequest(
            parts=[ToolReturnPart(tool_name="plan_show_progress", content="Progress 1", tool_call_id="id_show_1")],
            kind="request",
            timestamp=ts,
        ),
        # Message 9: plan_mark_step_complete (NEW) - Call
        ModelResponse(
            parts=[ToolCallPart(tool_name="plan_mark_step_complete", args={"step_id": 2}, tool_call_id="id_mark_2")],
            kind="response",
            timestamp=ts,
            usage=RequestUsage(),
        ),
        # Message 10: plan_mark_step_complete (NEW) - Return
        ModelRequest(
            parts=[
                ToolReturnPart(tool_name="plan_mark_step_complete", content="Step 2 done", tool_call_id="id_mark_2")
            ],
            kind="request",
            timestamp=ts,
        ),
        # Message 11: plan_show_progress (NEW) - Call
        ModelResponse(
            parts=[ToolCallPart(tool_name="plan_show_progress", args={}, tool_call_id="id_show_2")],
            kind="response",
            timestamp=ts,
            usage=RequestUsage(),
        ),
        # Message 12: plan_show_progress (NEW) - Return
        ModelRequest(
            parts=[ToolReturnPart(tool_name="plan_show_progress", content="Progress 2", tool_call_id="id_show_2")],
            kind="request",
            timestamp=ts,
        ),
        # Message 13: Mixed content (Text + ToolCall)
        # We want to test that if a message has text AND a redundant tool call, the tool call is removed but text remains.
        # This one (id_show_3) will be made redundant by a later call.
        ModelResponse(
            parts=[
                TextPart(content="Thinking..."),
                ToolCallPart(tool_name="plan_show_progress", args={}, tool_call_id="id_show_3_mixed"),
            ],
            kind="response",
            timestamp=ts,
            usage=RequestUsage(),
        ),
        # Message 14: Return for id_show_3_mixed (should be removed)
        ModelRequest(
            parts=[
                ToolReturnPart(tool_name="plan_show_progress", content="Progress 3", tool_call_id="id_show_3_mixed")
            ],
            kind="request",
            timestamp=ts,
        ),
        # Message 15: plan_show_progress (NEWEST) - Call
        # This makes id_show_2 and id_show_3_mixed redundant.
        ModelResponse(
            parts=[ToolCallPart(tool_name="plan_show_progress", args={}, tool_call_id="id_show_4")],
            kind="response",
            timestamp=ts,
            usage=RequestUsage(),
        ),
        # Message 16: plan_show_progress (NEWEST) - Return
        ModelRequest(
            parts=[ToolReturnPart(tool_name="plan_show_progress", content="Progress 4", tool_call_id="id_show_4")],
            kind="request",
            timestamp=ts,
        ),
    ]

    # Process
    new_history = planning.plan_history_processor(history)

    # Assertions

    # Should keep:
    # Msg 0 (User)
    # Msg 3, 4 (plan_create 2)
    # Msg 9, 10 (plan_mark_step_complete 2)
    # Msg 13 (Mixed - modified)
    # Msg 15, 16 (plan_show_progress 4)

    # Should remove:
    # Msg 1, 2 (plan_create 1)
    # Msg 5, 6 (plan_mark_step_complete 1)
    # Msg 7, 8 (plan_show_progress 1)
    # Msg 11, 12 (plan_show_progress 2)
    # ToolCallPart from Msg 13
    # Msg 14 (Return for mixed)

    # Verify contents
    # Helper to collect tool call ids present
    present_tool_calls = set()
    for m in new_history:
        for p in m.parts:
            if isinstance(p, ToolCallPart):
                present_tool_calls.add(p.tool_call_id)
            elif isinstance(p, ToolReturnPart):
                # We can also track returns if we want strict checking
                present_tool_calls.add(p.tool_call_id)

    assert "id_create_1" not in present_tool_calls
    assert "id_create_2" in present_tool_calls
    assert "id_mark_1" not in present_tool_calls
    assert "id_mark_2" in present_tool_calls
    assert "id_show_1" not in present_tool_calls
    assert "id_show_2" not in present_tool_calls
    assert "id_show_3_mixed" not in present_tool_calls
    assert "id_show_4" in present_tool_calls

    # Find the mixed message (should be index 5 in the new list?)
    # List: 0(User), 1-2(create2), 3-4(mark2), 5(Mixed), 6-7(show4) -> 8 messages
    assert len(new_history) == 8

    mixed_msg = new_history[5]
    # Should be ModelResponse
    assert isinstance(mixed_msg, ModelResponse)
    # Should have 1 part (TextPart)
    assert len(mixed_msg.parts) == 1
    assert isinstance(mixed_msg.parts[0], TextPart)
    assert mixed_msg.parts[0].content == "Thinking..."
