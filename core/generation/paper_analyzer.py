"""
Responsibility : Given a paper dict, produce a single structured analysis 
                 covering summary, keywords, contribution, and domain.
"""


import json
import re
import os
from groq import Groq 
from dotenv import load_dotenv
from config import GROQ_MODEL

load_dotenv()
_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ── Context selection ──────────────────────────────────────────────────────────

def _select_context(paper: dict) -> tuple[str, list[str]]:
    """
    Chooses which parts of the paper to send for analysis.
    """

    abstract = paper.get("abstract", "")
    chunk_data = paper.get("chunks", [])

    # chunk_data is list of (text, embedding) tuples -  we only need text
    all_texts = [text for text, _ in chunk_data]

    if len(all_texts) <= 8:
        selected = all_texts
    else:
        # First 5(intro area) + last 2 (conclusion area)
        selected = all_texts[:5] + all_texts[-2:]

    return abstract, selected

# ── Prompt ────────────────────────────────────────────────────────────────────

def _build_analysis_prompt(abstract: str, chunks: list[str]) -> str:
    chunks_text = ""
    for i, chunk in enumerate(chunks, 1):
        chunks_text += f"section {i}\n{chunk.strip()}\n\n"
    
    return f"""Analyze the following research paper and return a structured JSON analysis.

    Return only the JSON object. Do not add explanation, markdown, or extra fields.

    {{
        "summary": "5-8 sentence executive summary covering the problem, approach, and findings",
        "keywords": ["term1", "term2", "term3"],
        "contributions": "2-3 sentences describing the main contribution or novelty",
        "domain": "Primary research domain (e.g. Natural Language Processing)" 
    }}
    
    Keywords: 5-10 specific technical terms. Avoid generic words like model, method, paper, results.

    Abstract:
    {abstract}

    Paper Content:
    {chunks_text}"""

def _parse_response(raw: str) -> dict:
    """
    Parses the JSON string returned by the LLM.
    """

    try: 
        clean = raw.strip()
        # Defensive: strip markdown fences if somehow present
        if clean.startswith("```"):
            clean = re.sub(r"```(?:json)?\n?","",clean).strip().rstrip("`")
        
        data = json.loads(clean)

        # Normalize keywords - some models return [{"term"} : "x"] instead of ["x"]
        kws = data.get("keywords", [])
        if kws and isinstance(kws[0], dict):
            data["keywords"] = [
                k.get("term", k.get("keyword", str(k))) for k in kws
            ]

        return data
    
    except Exception as e:
        print(f"[Analyzer] JSON parse failed: {e}. Using fallback.")
        return {
            "summary":      raw[:800] if raw else "Analysis unavailable.",
            "keywords":     [],
            "contribution": "Could not extract contribution.",
            "domain":       "Unknown",
        }

# ── Main class ────────────────────────────────────────────────────────────────

class PaperAnalyzer:
    """
    paper dict -> structured analysis dict, via a single LLM call.
    """

    def __init__(self, model: str = GROQ_MODEL):
        self.model = model

    def analyze(self, paper: dict) -> dict:
        
        abstract, chunks = _select_context(paper)

        if not chunks and not abstract:
            return {
                "summary":    "No content available to analyze.",
                "keywords":    [],
                "contribution": "No content available.",
                "domain":       "Unknown",
            }
        
        prompt = _build_analysis_prompt(abstract, chunks)

        response = _client.chat.completions.create(
            model = self.model,
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a research paper analyst."
                        "Always respond with valid JSON only."
                        "No explanation, no markdown."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            response_format = {"type": "json_object"},
            temperature=0.1,
            max_tokens = 800,
        )

        raw = response.choices[0].message.content
        result = _parse_response(raw)

        print(
            f"[Analyze] Done - domain: {result.get('domain')}, "
            f"keywords: {len(result.get('keywords', []))}"
        )
        return result


# Module-level singleton - created once at import, reused across all requests
analyzer = PaperAnalyzer()