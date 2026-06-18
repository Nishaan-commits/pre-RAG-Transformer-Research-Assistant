"""
embedding.py — lazy-loaded version
 
Why this change?
    The old version loaded the model at import time:
        embedding_model = load_embedding_model()
    This ran the instant uvicorn imported api.py — before the server
    could bind its port. On a memory-constrained host like Render's
    free tier, that delay (or the memory spike during loading) caused
    the port-scan timeout.
 
    Now the model loads on the FIRST actual request, not at startup.
    The server binds its port in milliseconds; the model loads lazily
    the first time someone actually searches or asks a question.
"""


from sentence_transformers import SentenceTransformer
from config import EMBED_MODEL_PATH, EMBED_MODEL_NAME
import os

_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if os.path.isdir(EMBED_MODEL_PATH):
        print("[Embedding] Loading model from local cache...")
        _embedding_model = SentenceTransformer(EMBED_MODEL_PATH)
    
    else:
        print("Downloading embedding model")
        _embedding_model = SentenceTransformer(EMBED_MODEL_NAME)
        _embedding_model.save(EMBED_MODEL_PATH)
    
    return _embedding_model


def create_embeddings(chunks):
    model = get_embedding_model()
    embeddings = model.encode(
        chunks,
        batch_size=32,
        show_progress_bar=True,
        convert_to_tensor=False,  # numpy directly, no need to .cpu() later
        normalize_embeddings=True  # ✅ replaces your F.normalize step
    )
    # pair each chunk with its embedding vector
    return list(zip(chunks, embeddings))