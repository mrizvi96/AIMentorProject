"""
Custom LLM wrapper for llama.cpp server running Mistral-7B
"""
from typing import Any
import requests
from llama_index.core.llms import CustomLLM, CompletionResponse, LLMMetadata
from llama_index.core.llms.callbacks import llm_completion_callback


class MistralLLM(CustomLLM):
    """Custom LLM that connects to llama.cpp server"""

    context_window: int = 4096
    num_output: int = 512
    model_name: str = "mistral-7b"
    server_url: str = "http://localhost:8080"
    temperature: float = 0.7

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=self.context_window,
            num_output=self.num_output,
            model_name=self.model_name,
        )

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        """Call llama.cpp server for completion"""
        print(f"Prompt: {prompt}")
        response = requests.post(
            f"{self.server_url}/v1/completions",
            json={
                "prompt": prompt,
                "max_tokens": kwargs.get("max_tokens", self.num_output),
                "temperature": kwargs.get("temperature", self.temperature),
                "stop": kwargs.get("stop", ["\n\n"]),
            },
            timeout=300
        )
        response.raise_for_status()
        result = response.json()

        return CompletionResponse(
            text=result["choices"][0]["text"],
            raw=result,
        )

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs: Any):
        """Streaming not implemented for now"""
        return self.complete(prompt, **kwargs)
