from __future__ import annotations

from dataclasses import dataclass, field, replace

from pydantic_ai import FunctionToolset, RunContext
from pydantic_ai.messages import (
    ModelMessage,
    ToolCallPart,
    ToolReturnPart,
)

from .utils import EnumerateMessageWithParts


@dataclass
class PlanStep:
    id: int
    description: str
    completed: bool = False


@dataclass
class PlanningContext:
    steps: list[PlanStep] = field(default_factory=list)

    def __str__(self) -> str:
        if not self.steps:
            return "No plan created yet."

        lines = ["Current Plan:"]
        for step in self.steps:
            status = "[x]" if step.completed else "[ ]"
            lines.append(f"{status} {step.id}. {step.description}")
        return "\n".join(lines)


def _get_context(ctx: RunContext[object]) -> PlanningContext:
    target = ctx.deps if ctx.deps is not None else ctx

    if not hasattr(target, "_planning_context"):
        # A hackey way to add private deps to the context
        target._planning_context = PlanningContext()  # type: ignore[attr-defined]

    context = target._planning_context  # type: ignore[attr-defined]
    if not isinstance(context, PlanningContext):
        raise TypeError("Planning context is not an instance of PlanningContext")  # noqa: TRY003 long exception message

    return context


def plan_create(ctx: RunContext[object], steps: list[str]) -> str:
    """Create a new plan with the given steps. Use this to initialize the plan."""
    p_ctx = _get_context(ctx)
    p_ctx.steps = [PlanStep(id=i + 1, description=s) for i, s in enumerate(steps)]
    return str(p_ctx)


def plan_mark_step_complete(ctx: RunContext[object], step_id: int) -> str:
    """Mark a step as complete by its ID."""
    p_ctx = _get_context(ctx)
    found = False
    for step in p_ctx.steps:
        if step.id == step_id:
            step.completed = True
            found = True
            break

    if not found:
        return f"Step {step_id} not found."

    return str(p_ctx)


def plan_show_progress(ctx: RunContext[object]) -> str:
    """Show the current progress of the plan."""
    p_ctx = _get_context(ctx)
    return str(p_ctx)


def plan_history_processor(ctx: RunContext[object], history: list[ModelMessage]) -> list[ModelMessage]:
    """
    Process the history to keep only the most recent planning tool calls.

    This function scans the entire history and keeps only the most recent
    create_plan / plan_mark_step_complete / plan_show_progress for each of them.
    It removes the entire pair (ToolCall and ToolReturn) for redundant calls.
    """
    planning_tools = {plan_create.__name__, plan_mark_step_complete.__name__, plan_show_progress.__name__}

    # Collect tool_call_ids to remove by scanning backwards
    ids_to_remove: set[str] = set()
    found_tools: set[str] = set()

    for _, parts in EnumerateMessageWithParts(reversed(history)):
        for part in reversed(parts):
            if isinstance(part, ToolCallPart) and part.tool_name in planning_tools:
                if part.tool_name in found_tools and part.tool_call_id:
                    ids_to_remove.add(part.tool_call_id)
                else:
                    found_tools.add(part.tool_name)

    # Reconstruct history filtering out marked calls and their returns
    new_history: list[ModelMessage] = []
    for message, parts in EnumerateMessageWithParts(history):
        new_parts = []
        original_parts_count = len(parts)

        for part in parts:
            if isinstance(part, (ToolCallPart, ToolReturnPart)) and part.tool_call_id in ids_to_remove:
                continue
            new_parts.append(part)

        if not new_parts:
            # If the message became empty after removal, skip it
            pass
        elif len(new_parts) == original_parts_count:
            new_history.append(message)
        else:
            # Create a new message with filtered parts using replace
            # Ignore type check because we don't have a good type for new parts
            new_history.append(replace(message, parts=new_parts))  # type: ignore[arg-type]

    return new_history


TOOLSET: FunctionToolset[object] = FunctionToolset(tools=[plan_create, plan_mark_step_complete, plan_show_progress])

INSTRUCTION = """
Planning System Instructions:
1. Before processing any request, you MUST call 'plan_create' to generate a step-by-step plan.
2. Execute the plan step by step.
3. After completing each step, you MUST call 'plan_mark_step_complete' to mark it as done.
4. You can check your progress using 'plan_show_progress'.
5. Follow the plan strictly.
"""

HISTORY_PROCESSOR = plan_history_processor
