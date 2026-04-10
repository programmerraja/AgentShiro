from litellm.llms.custom_llm import CustomLLM

class BaseCustomLLM(CustomLLM):
    """
    In case we want to standardize methods across multiple custom providers,
    we can define our BaseCustomLLM that inherits from litellm's CustomLLM.
    """
    def __init__(self):
        super().__init__()
