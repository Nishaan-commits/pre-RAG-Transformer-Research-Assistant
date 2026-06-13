"""
Wraps the Existing VectorStore as a LangChain BaseRetriever.

Why wrap ?
        LangChain has langchain_community.vectorstores.FAISS - it would rebuild
        everything from scratch. That erases the learning value of what we built.

        Wrapping means:
            - Your FAISS index, embedding logic, and search stay exactly as they are
            - LangChain gets a clean interface it can plug into any chain.
            - You can see exactly where your code ends and LangChain begins

What BaseRetriever expects:
    One method: _get_relevant_documents(query) -> list[Document]
    That's the entire contract. Anything that implements it is a retriever.

What Document is:
    Langchain's standard unit of text. Two fields:
        page_content: str   - the actual text
        metadata: dict      - anything else (source, index, score, etc.)        

    Your VectorStore returns list[str].
    This wrapper converts those strings into Document objects.
    That's the entire job of this file.
"""

from typing import Any
from pydantic import ConfigDict
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun

from core.retrieval.vector_store import VectorStore


class VectorStoreRetriever(BaseRetriever):
    
    model_config = ConfigDict(arbitrary_types_allowed=True)

    vector_store : VectorStore
    top_k: int = 5

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:

        chunk_texts = self.vector_store.search(query, top_k=self.top_k)

        return [
            Document(
                page_content = chunk,
                metadata={
                    "chunk_index": i,
                    # Add more metadata here later if needed:
                    # "source": paper_title, "score": similarity_score, etc. 
                },
            )
            for i, chunk in enumerate(chunk_texts)
        ]



