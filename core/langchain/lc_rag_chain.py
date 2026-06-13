"""
Key new Concept: RunnablePassThrough and the dict fan-out pattern.
"""

import os
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from core.retrieval.vector_store import VectorStore
from core.langchain.lc_retriever import VectorStoreRetriever
from config import GROQ_MODEL
from dotenv import load_dotenv

load_dotenv()

# ── Prompt ───────────────
_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        (
            "You are a research assistant specialized in academic papers. "
            "Answer ONLY using the provided context. Do not use outside knowledge. "
            "Reference relevant chunk numbers when answering "
            "(e.g. 'According to Chunk 2...'). "
            "If you can infer an answer from all the chunks provided then infer it and label it as inference"
            "If the answer is neither in the context nor inferred, say exactly: "
            "'I could not find the answer in the provided context.'"
        ),
    ),
    (
        "human",
        "Context:\n{context}\n\nQuestion: {question}",
    ),
])

# ── LLM ───────────────────────────────────────────────────────────────────────
_llm = ChatGroq(model=GROQ_MODEL, temperature=0.2, max_tokens=512)

# ── Output parser ─────────────────────────────────────────────────────────────
_parser = StrOutputParser()

# ── Document formatter ────────────────────────────────────────────────────────

def _format_docs(docs: list[Document]) -> str:
    return "\n\n".join(
        f"[Chunk {i + 1}]\n {doc.page_content.strip()}"
        for i, doc in enumerate(docs)
    )

# ── Chain factory ─────────────────────────────────────────────────────────────

def build_rag_chain(vector_store: VectorStore, top_k: int = 5):
    """
    Why a factory function instead of a module-level chain?
        The retriever needs a VectorStore instance, which is paper-specific.
        Each paper has its own FAISS index stored in PaperSession.store.
        A module-level chain would need to know about the paper at import time,
        which is impossible. A factory creates a fresh chain per paper.
 
    The chain structure — LCEL dict fan-out:
 
        question (str)
             │
             ├──────────────────────────────────────┐
             │                                      │
             ▼                                      ▼
        retriever                         RunnablePassthrough()
        (FAISS search)                    (passes question unchanged)
             │                                      │
             ▼                                      │
        list[Document]                              │
             │                                      │
             ▼                                      │
        _format_docs()                              │
        (→ context string)                          │
             │                                      │
             └──────────────┬───────────────────────┘
                            │
                            ▼
                  {"context": "...", "question": "..."}
                            │
                            ▼
                        _prompt
                  (fills both variables)
                            │
                            ▼
                          _llm
                      (calls Groq)
                            │
                            ▼
                        _parser
                  (extracts string)
                            │
                            ▼
                    answer (str)
 
    The dict {"context": ..., "question": ...} is LCEL's fan-out syntax.
    Each key becomes a template variable. Each value is a Runnable that
    receives the original input (the question string) and produces that variable.
 
    RunnablePassthrough() is the identity function as a Runnable:
        input → output unchanged
    It's how you say "this variable IS the input, don't transform it."
 
    RunnableLambda(_format_docs) wraps a plain Python function as a Runnable.
    Any function can become a chain step this way.
    """

    retriever = VectorStoreRetriever(vector_store=vector_store, top_k=top_k)

    rag_chain = (
        {
            # Left branch: question -> retrieve docs -> format as string
            "context" :  retriever | RunnableLambda(_format_docs),
            # Right branch: question -> pass through unchanged
            "question": RunnablePassthrough(),
        }
        | _prompt
        | _llm
        | _parser
    )

    return rag_chain

# ── Convenience wrapper ────────────────────────────────────────────────────────

def lc_rag_answer(question: str, vector_store: VectorStore, top_k: int = 5) -> str:
    """
    One-call interface for paper_assistant.py.
    """
    chain = build_rag_chain(vector_store, top_k)
    return chain.invoke(question)