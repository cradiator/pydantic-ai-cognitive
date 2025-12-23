from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)


def dump_history(history: list[ModelMessage]):
    """
    Dump the history in a human-readable format.
    """
    print(f"\n{'=' * 20} HISTORY DUMP ({len(history)} messages) {'=' * 20}")
    for i, msg in enumerate(history):
        role = "UNKNOWN"
        if isinstance(msg, ModelRequest):
            role = "USER (or Tool Return)"
        elif isinstance(msg, ModelResponse):
            role = "MODEL"

        print(f"\n[{i}] {role} (timestamp: {msg.timestamp}):")
        for part in msg.parts:
            if isinstance(part, UserPromptPart):
                print(f"  User Prompt: {part.content}")
            elif isinstance(part, TextPart):
                print(f"  Text: {part.content}")
            elif isinstance(part, ToolCallPart):
                print(f"  Tool Call: {part.tool_name}({part.args}) [ID: {part.tool_call_id}]")
            elif isinstance(part, ToolReturnPart):
                print(f"  Tool Return: {part.tool_name} [ID: {part.tool_call_id}]")
                print(f"    Result: {part.content}")
            else:
                print(f"  Unknown Part: {part}")
    print(f"{'=' * 60}\n")
    return history
