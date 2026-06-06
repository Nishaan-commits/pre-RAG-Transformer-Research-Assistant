"""

Responsibility: Store embeddings in a FAISS index and retrieve the most relevant chunks for a given query.

"""

import faiss 
import numpy as np 
import pickle 
import os
from core.retrieval.embedding import embedding_model

class VectorStore:
    """

    Wraps a FAISS index + a chunk text list.

    """

    def __init__(self):
        self.index = None
        self.chunks = []

    def build_index(self, chunk_embeddings: list[tuple[str, np.ndarray]]):
        """

        Builds the FAISS index from (chunk_text, embedding) pairs.

        Why numpy float32?
        FAISS is written in C++ and require float32 arrats specifically.
        SentenceTransformers gives float32 by default, but we cast anyways to be safe
        - silent type bugs are the worst kind.

        """

        # seperate text from vectors
        self.chunks = [chunk for chunk, _ in chunk_embeddings]
        embeddings = np.array([emb for _, emb in chunk_embeddings], dtype="float32")

        dim = embeddings.shape[1]

        # IndexFlatIP: exact search using inner product 
        # = cosine similarity when vectors are L2-normalized
        self.index = faiss.IndexFlatIP(dim)

        self.index.add(embeddings)

        print(f"[VectorStore] Index built - {self.index.ntotal} chunks indexed.")
    
    def search(self, query: str, top_k: int = 5) -> list[str]:
        """

        Returns the top_k most relevant chunk texts for a query string.

        """

        if self.index is None:
            raise RuntimeError(
                "Index is empty. Call build_index() before searching."
            )
        
        query_vector = embedding_model.encode(
            [query],
            normalize_embeddings=True,
            convert_to_tensor = False
        ).astype("float32")

        # FAISS search
        distances, indices = self.index.search(query_vector, top_k)

        results = [
            self.chunks[i]
            for i in indices[0]
            if i != -1
        ]

        return results

    def save_index(self, index_path:str, chunks_path: str):
        """ 

        Saves the FAISS index and chunk list to disk.

        """

        if self.index is None:
            raise RuntimeError("Nothing to save - index has not been built yet.")

        os.makedirs(os.path.dirname(index_path), exist_ok=True)

        faiss.write_index(self.index, index_path)

        with open(chunks_path, "wb") as f:
            pickle.dump(self.chunks, f)
        
        print(f"[VectorStore] Saved - {self.index.ntotal} vectors -> {index_path}")

    def load_index(self, index_path: str, chunks_path: str):
        """
        Restores a previously saved index from disk.
        """

        if not os.path.exists(index_path):
            raise FileNotFoundError(f"No FAISS index found at: {index_path}")

        if not os.path.exists(chunks_path):
            raise FileNotFoundError(f"No chunks file found at: {chunks_path}")

        self.index = faiss.read_index(index_path)

        with open(chunks_path, "rb") as f:
            self.chunks = pickle.load(f)
        
        print(f"[VectorStore] Loaded - {self.index.ntotal} vectors from {index_path}")