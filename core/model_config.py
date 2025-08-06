MODEL_CONFIG = {
    "obsidianai": [
        {"name": "gpt-4o-mini", "status": "active"},
    ],
    "azureai": [
        {"name": "gemini-2.0-flash-lite-001", "status": "active"},
    ],
    "crimsonai": [
        {"name": "deepseek-chat", "status": "active"},
    ],
    "gemini": [
        {"name": "gemini-2.5-flash", "status": "active"},
        {"name": "gemini-1.5-flash", "status": "inactive"},
        {"name": "gemini-2.0-flash", "status": "inactive"},
    ],
    "gpt": [
        {"name": "gpt-4.1-mini", "status": "active"},
    ],
    # Add more providers and their models as needed
}

def get_active_model(model_or_provider: str) -> str:
    """
    Returns the active model name for the given provider.
    If a specific model name is given, returns it directly.
    If a provider name is given, returns the active model for that provider.
    """
    # If exact model name is present in any provider, return it
    for models in MODEL_CONFIG.values():
        for model in models:
            if model["name"].lower() == model_or_provider.lower():
                return model["name"]
    # Otherwise, treat as provider and return its active model
    provider = model_or_provider.lower()
    if provider in MODEL_CONFIG:
        for model in MODEL_CONFIG[provider]:
            if model.get("status") == "active":
                return model["name"]
    return model_or_provider  # fallback
