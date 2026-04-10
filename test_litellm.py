from litellm.utils import Message, Choices, ModelResponse
msg = Message(role="assistant", content="test", tool_calls=[{"id": "call_1", "type": "function", "function": {"name": "test", "arguments": "{}"}}])
try:
    print(msg.tool_calls[0].id)
    print("Success with dict")
except Exception as e:
    print("Dict failed", e)

try:
    class F:
        def __init__(self):
            self.name = "test"
            self.arguments = "{}"
    class TC:
        def __init__(self):
            self.id= "call_1"
            self.type="function"
            self.function = F()
    msg = Message(role="assistant", content="test", tool_calls=[TC()])
    print(msg.tool_calls[0].id)
    print("Success with object")
except Exception as e:
    print("Object failed", e)
