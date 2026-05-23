import os
from kase.providers import registry
from kase.providers.base import ProviderProfile

def check_vertex():
    return bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("VERTEX_PROJECT_ID"))

registry.register_provider(ProviderProfile(
    name="vertex",
    display_name="Google Vertex AI",
    api_mode="chat_completions",
    base_url="",
    env_key="GOOGLE_APPLICATION_CREDENTIALS",
    models=["gemini-2.5-pro", "gemini-2.0-flash", "claude-3-5-sonnet"],
    context_length=1048576,
    check_fn=check_vertex,
))
