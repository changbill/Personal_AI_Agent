"""One place that builds the Ollama model, so the local-LLM policy is applied once.

think=false keeps the model from spending CPU on chain-of-thought during short routing
and tool-selection decisions. num_ctx is pinned low so the KV cache cannot eat the mini
PC RAM. Both paths were verified against the Strands request builder and a real call.
"""

from strands.models.ollama import OllamaModel

from app.core.config import Settings


def build_ollama_model(settings: Settings) -> OllamaModel:
    """Create the shared local model configuration."""
    return OllamaModel(
        host=settings.ollama_host,
        model_id=settings.ollama_model,
        additional_args={"think": False},
        options={"num_ctx": settings.ollama_num_ctx},
        temperature=0,
    )
