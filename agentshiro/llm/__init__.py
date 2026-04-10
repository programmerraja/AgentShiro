import litellm
from .custom import ShiroCustomProvider

# Register the standard handler instance
shiro_custom_handler = ShiroCustomProvider()

# Map the "shiro-custom" prefix to our custom handler in LiteLLM
litellm.custom_provider_map = [
    {"provider": "LiquidAI", "custom_handler": shiro_custom_handler}
]


def completion(*args, **kwargs):
    """
    Wrapper around litellm.completion.
    If 'model' starts with 'shiro-custom/', it will invoke ShiroCustomProvider!
    """
    return litellm.completion(*args, **kwargs)
