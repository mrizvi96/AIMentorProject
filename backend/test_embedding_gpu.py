import os
os.environ.pop('HF_HUB_ENABLE_HF_TRANSFER', None)

import torch
print("Testing if sentence-transformers can use GPU...")
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Test with explicit CUDA device
try:
    embed_model = HuggingFaceEmbedding(
        model_name="all-MiniLM-L6-v2",
        device="cuda"
    )
    print(f"✓ Embedding model created successfully")
    
    # Test a simple embedding
    embeddings = embed_model.get_text_embedding("This is a test sentence.")
    print(f"✓ Generated embedding of length: {len(embeddings)}")
    
    # Check GPU memory
    if torch.cuda.is_available():
        print(f"GPU memory allocated: {torch.cuda.memory_allocated(0) / 1024**2:.2f} MB")
        print(f"GPU memory cached: {torch.cuda.memory_reserved(0) / 1024**2:.2f} MB")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
