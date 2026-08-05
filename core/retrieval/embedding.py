"""
embedding.py — HuggingFace Inference API version
 
Replaces the local SentenceTransformer model with API calls to HF.
Memory impact: drops from ~300MB (local model) to ~0MB at idle.
 
What stays identical:
  - Output shape: (n, 384) float32 numpy array, L2-normalized
  - create_embeddings() interface: list[str] → list[(str, np.ndarray)]
  - Everything in vector_store.py, chunker.py, paper_assistant.py
 
What changes:
  - No model loaded locally
  - Embeddings computed via HTTP POST to HF servers
  - ~100-200ms latency per batch (fine for a portfolio demo)
  - Requires HF_TOKEN environment variable
"""



import time
import os
import numpy as np
import requests
from dotenv import load_dotenv

load_dotenv()

# Config 


HF_TOKEN = os.getenv("HF_TOKEN")
assert HF_TOKEN is not None, "HF_TOKEN is None"

print("repr:", repr(HF_TOKEN))
print("length:", len(HF_TOKEN))
print("startswith hf_:", HF_TOKEN.startswith("hf_"))

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
API_URL = (
    f"https://router.huggingface.co/"
    f"hf-inference/models/{MODEL_ID}/pipeline/feature-extraction"
)
HEADERS  = {"Authorization": f"Bearer {HF_TOKEN}"}

# How many chunks to send per API call.
# HF free tier has a request size limit. 32 chunks x ~400 tokens each
# stays comfortably under it and matches old batch_size = 32. 
BATCH_SIZE = 32

# Core API call

def _embed_batch(texts: list[str], retries: int = 5) -> np.ndarray:

    payload = {"inputs": texts, "options": {"wait_for_model": True}}

    for attempt in range(retries):
        print("Authorization header:",
              headers["Authorization"][:15] + "...")
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)

        if response.status_code == 200:
            # Response is list of lists: [[],[],...]
            embeddings = np.array(response.json(), dtype="float32")

            # Normalize each vector
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)

            # Avoid division by zero for any vectors 
            norms = np.where(norms == 0, 1, norms)
            embeddings = embeddings / norms

            return embeddings

        elif response.status_code == 503:
          # Model is cold-starting - wait and retry
          wait = (attempt + 1) * 10
          print(f"[Embedding] HF model loading, waiting {wait}s (attempt {attempt + 1}/{retries})...")
          time.sleep(wait)
        
        else:
          # Unexpected error - raise immediately, don't retry
          raise RuntimeError(
              f"""
          Status: {response.status_code}
          Headers: {dict(response.headers)}
          Body: {response.text}
          """
          )
    
    raise RuntimeError(
      f"HF model did not become ready after {retries} retries. "
      "Check your HF_TOKEN and model availability."
    )


def create_embeddings(chunks: list[str]) -> list[tuple[str, np.ndarray]]:
  """
  Embeds a list of chunk strings via HF Inference API.
  """
  if not chunks:
    return []

  if not HF_TOKEN:
    raise RuntimeError(
      "HF_TOKEN not found. Add it to your .env file and Render env vars."
    )

  all_embeddings = []

  for i in range(0, len(chunks), BATCH_SIZE):
    batch = chunks[i : i + BATCH_SIZE]
    print(f"[Embedding] Batch {i // BATCH_SIZE + 1} / {len(chunks) // BATCH_SIZE + 1}")
    batch_embeddings = _embed_batch(batch)
    all_embeddings.append(batch_embeddings)

  # Concatenate all batches into one matrix, then split into per_chunk vectors
  embeddings_matrix = np.vstack(all_embeddings)  # shape: (num_chunks, 384)

  return list(zip(chunks, embeddings_matrix))

def get_query_embedding(text: str) -> np.ndarray:
  """
  Embeds a single query string for use in vector_store.search().
  
  Kept seperate from create_embeddings() because:
  - Queries are always single strings, not batches
  - Called at query time, not at index-build time
  - Makes vector_store.py's import clean and explicit

  Returns:
      1D numpy array of shape (384,), float32, L2-normalized
  """
  
  result = _embed_batch([text]) # shape: (1, 384)
  return result[0]              # shape: (384,)
  
