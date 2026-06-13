import os
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel, Field 
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from config import GROQ_MODEL

load_dotenv()

# ── Schema definition ──────────────────────────────────────────────────────────
#
# BaseModel is Pydantic's base class. Inheriting from it gives you:
#   - Type validation on every field at construction time
#   - .model_dump() to convert to a plain dict when needed
#
# Field(description=...) does two things:
#   1. Documents what the field means (like a docstring per field)
#   2. The PydanticOutputParser reads these descriptions and includes them
#      in the format instructions sent to the LLM — so the LLM knows not
#      just the field name but what it's supposed to contain

class PaperAnalysis(BaseModel):
    summary: str = Field(
        description = "5-8 sentence executive summary covering the problem, approach, and findings"
    )
    keywords: List[str] = Field(
        description = "5-10 specific technical terms relevant to the paper. No generic words like 'model' or 'method'."
    )
    contribution: str = Field(
        description = "2-3 sentences describing the main contribution or novelty of the paper"
    )
    domain: str = Field(
        description = "Primary research domain, e.g. 'Natural Language Processing' or 'Computer Vision'" 
    )

# ── Parser ─────────────────────────────────────────────────────────────────────
parser = PydanticOutputParser(pydantic_object=PaperAnalysis)

# ── Prompt ─────────────────────────────────────────────────────────────────────
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        (
            "You are a research paper analyst. "
            "Analyze the provided paper content and return a structured response "
            "following the format instructions exactly."
        ),
    ),
    (
        "human",
        "{format_instructions}\n\nAbstract:\n{abstract}\n\nPaper Content:\n{context}"
    ),
]).partial(format_instructions=parser.get_format_instructions())

# ── LLM ───────────────────────────────────────────────────────────────────────
llm = ChatGroq(
    model = GROQ_MODEL,
    temperature=0.1,
    max_tokens=800,
)

# ── Chain ──────────────────────────────────────────────────────────────────────
analysis_chain = prompt | llm | parser

def _select_context(paper: dict) -> tuple[str, str]:
    """
    Returns (abstract, formatted_context_string)
    """

    abstract = paper.get("abstract", "")
    chunk_data = paper.get("chunks", [])
    all_texts = [text for text, _ in chunk_data]

    selected = all_texts if len(all_texts) <= 8 else all_texts[:5] + all_texts[-2:]

    context = "\n\n".join(
        f"[Section {i}]\n{chunk.strip()}"
        for i, chunk in enumerate(selected, 1)
    )
    return abstract, context

# ── Public interface ───────────────────────────────────────────────────────────

def lc_analyze(paper: dict) -> dict:
    """ 
    Langchain + Pydantic version of analyzer.analyze().
    """
    abstract, context = _select_context(paper)

    if not context and not abstract:
        return {
            "summary":          "No content avilable to analyze.",
            "keywords":         [],
            "contribution":     "No content available.",
            "domain":           "Unknown",
        }

    try:
        analysis: PaperAnalysis = analysis_chain.invoke({
            "abstract": abstract,
            "context": context,
        })

        print(
            f"[LC Analyzer] Done - domain: {analysis.domain}, "
            f"keywords: {len(analysis.keywords)}"
        )

        return analysis.model_dump()
    
    except Exception as e:
        print(f"[LC Analyzer] Failed: {e}")
        return {
            "summary":      "Analysis failed. Please try again.",
            "keywords":     [],
            "contribution": "Could not extract contribution.",
            "domain":       "Unknown",
        }