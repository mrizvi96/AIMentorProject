"""
Custom Embedding Wrapper to Fix llama-cpp-python Response Format

The llama-cpp-python server returns embeddings as [[...]] (nested array)
but LlamaIndex expects [...] (flat array). This wrapper flattens the response.
"""
from typing import List
from llama_index.embeddings.openai import OpenAIEmbedding


class FlattenedOpenAIEmbedding(OpenAIEmbedding):
    """
    OpenAI-compatible embedding that flattens nested array responses
    from llama-cpp-python server.
    """

    def _get_query_embedding(self, query: str) -> List[float]:
        """Get embedding for a single query, flattening if needed"""
        embedding = super()._get_query_embedding(query)

        # If embedding is nested [[...]], flatten to [...]
        if embedding and isinstance(embedding[0], list):
            return embedding[0]

        return embedding

    def _get_text_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text, flattening if needed"""
        embedding = super()._get_text_embedding(text)

        # If embedding is nested [[...]], flatten to [...]
        if embedding and isinstance(embedding[0], list):
            return embedding[0]

        return embedding

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts, flattening if needed"""
        embeddings = super()._get_text_embeddings(texts)

        # Flatten each embedding if nested
        flattened = []
        for emb in embeddings:
            if emb and isinstance(emb[0], list):
                flattened.append(emb[0])
            else:
                flattened.append(emb)

        return flattened
