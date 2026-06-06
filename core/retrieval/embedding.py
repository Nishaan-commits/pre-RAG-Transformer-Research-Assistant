from sentence_transformers import SentenceTransformer
import torch
import torch.nn.functional as F
from config import EMBED_MODEL_PATH, EMBED_MODEL_NAME
import os


def load_embedding_model():
    if os.path.isdir(EMBED_MODEL_PATH):
        embedding_model = SentenceTransformer(EMBED_MODEL_PATH)
    
    else:
        print("Downloading embedding model")
        embedding_model = SentenceTransformer(EMBED_MODEL_NAME)
        model.save(EMBED_MODEL_PATH)
    
    return embedding_model
    
embedding_model = load_embedding_model()

# Mean Pooling Function
  # Transformers output token embeddings, but we want sentence embedding.

def mean_pooling(model_output, attention_mask):

  token_embeddings = model_output.last_hidden_state

  input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()

  return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
      input_mask_expanded.sum(1),
      min=1e-9
  )

# Embedding Function 

device = "cuda" if torch.cuda.is_available() else "cpu"

embedding_model.to(device)

def create_embeddings(chunks):
    embeddings = embedding_model.encode(
        chunks,
        batch_size=32,
        show_progress_bar=True,
        convert_to_tensor=False,  # numpy directly, no need to .cpu() later
        normalize_embeddings=True  # ✅ replaces your F.normalize step
    )
    # pair each chunk with its embedding vector
    return list(zip(chunks, embeddings))