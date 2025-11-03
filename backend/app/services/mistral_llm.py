"""
Custom LLM wrapper for llama.cpp server running Mistral-7B
"""
from typing import Any
import json
import requests
from llama_index.core.llms import CustomLLM, CompletionResponse, LLMMetadata
from llama_index.core.llms.callbacks import llm_completion_callback
from app.core.config import settings


class MistralLLM(CustomLLM):
    """Custom LLM that connects to llama.cpp server"""

    context_window: int = 4096  # Keep as reasonable default for LLaMA-based models
    num_output: int = settings.llm_max_tokens
    model_name: str = settings.llm_model_name
    server_url: str = settings.llm_base_url.rstrip('/v1')  # Remove /v1 suffix if present
    temperature: float = settings.llm_temperature

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
        try:
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
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(
                f"Failed to connect to LLM server at {self.server_url}. "
                f"Make sure the llama.cpp server is running on port {self.server_url.split(':')[-1].split('/')[0]}. "
                f"Error: {str(e)}"
            )
        except requests.exceptions.Timeout as e:
            raise RuntimeError(
                f"LLM server request timed out after 300 seconds. "
                f"The model may be overloaded or the request may be too complex. "
                f"Error: {str(e)}"
            )
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(
                f"LLM server returned error status {response.status_code}: {response.text}. "
                f"Error: {str(e)}"
            )
        except (KeyError, IndexError) as e:
            raise RuntimeError(
                f"LLM server returned unexpected response format. "
                f"Response: {result if 'result' in locals() else 'No response'}. "
                f"Error: {str(e)}"
            )

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs: Any):
        """Streaming completion with error handling"""
        try:
            response = requests.post(
                f"{self.server_url}/v1/completions",
                json={
                    "prompt": prompt,
                    "max_tokens": kwargs.get("max_tokens", self.num_output),
                    "temperature": kwargs.get("temperature", self.temperature),
                    "stop": kwargs.get("stop", ["\n\n"]),
                    "stream": True,
                },
                timeout=300,
                stream=True,
            )
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        json_data = decoded_line[6:]
                        if json_data != "[DONE]":
                            data = json.loads(json_data)
                            yield CompletionResponse(
                                text=data["choices"][0]["text"],
                                raw=data,
                            )
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(
                f"Failed to connect to LLM server at {self.server_url}. "
                f"Make sure the llama.cpp server is running. "
                f"Error: {str(e)}"
            )
        except requests.exceptions.Timeout as e:
            raise RuntimeError(
                f"LLM server streaming request timed out. "
                f"Error: {str(e)}"
            )
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(
                f"LLM server returned error status {response.status_code}: {response.text}. "
                f"Error: {str(e)}"
            )
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            raise RuntimeError(
                f"LLM server returned malformed streaming response. "
                f"Error: {str(e)}"
            )

    @llm_completion_callback()
    def stream_chat(self, messages, **kwargs: Any):
        """Streaming chat endpoint"""
        prompt = self.messages_to_prompt(messages)
        return self.stream_complete(prompt, **kwargs)
