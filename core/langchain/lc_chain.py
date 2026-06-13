"""
LangChain replacement for the combination of:
    prompt_builder.py -> build_prompt() 
    llm_client.py     -> generate_answer()
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import GROQ_MODEL

load_dotenv()

llm = ChatGroq(
    model=GROQ_MODEL,
    temperature=0.2,
    max_tokens=512,
)

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        (
            "You are a research assistant specialized in academic papers. "
            "Answer ONLY using the provided context. Do not use outside knowledge. "
            "When answering, reference relevant chunk numbers "
            "(e.g. 'According to Chunk 2...'). "
            "If the answer is not in the context, respond with exactly: "
            "'I could not find the answer in the provided context.'"            
            "If the answer can be reasonably inferred by combining information from the context, provide the inference and clearly label it as an inference."
        ),
    ),
    (
        "human",
        "Context:\n{context}\n\nQuestion: {question}",
    ),
])

parser = StrOutputParser()

chain = prompt | llm | parser

# ── Helpers ───────────────────────────────────────────────────────────────────

def _format_context(chunks: list[str]) -> str:
    """
    Converts chunk list to numbered context string.
    """
    return "\n\n".join(
        f"[Chunk {i}]\n{chunk.strip()}"
        for i, chunk in enumerate(chunks, 1)
    )

# ── Public interface ───────────────────────────────────────────────────────────

def lc_generate(question: str, chunks: list[str]) -> str:
    context = _format_context(chunks)
    return chain.invoke({"question": question, "context": context})