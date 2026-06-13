from core.ingestion.arxiv_fetcher import search_papers, download_pdf_from_metadata
from core.processing.preprocessing import preprocess_paper
from core.processing.chunker import create_chunks
from core.retrieval.embedding import create_embeddings
from core.retrieval.vector_store import VectorStore
from core.qa.QA_model import answer_question
from core.generation.prompt_builder import build_prompt
from core.generation.llm_client import generate_answer
from core.generation.paper_analyzer import analyzer
from core.langchain.lc_chain import lc_generate
from core.langchain.lc_parser import lc_analyze
from core.langchain.lc_rag_chain import build_rag_chain, lc_rag_answer
from config import GROQ_MODEL

def fetch_papers(query: str, max_results: int = 5) -> list[dict]:
    """
    Returns metadata-only paper list. This is what /search calls.
    """
    return search_papers(query, max_results)


def process_paper(query, max_results=5):
    papers = extractor(query, max_results=max_results)
    processed_papers = []
    for P in papers:

        try:

            # Text Extraction
            P['text'] = preprocess_paper(P['pdf_path'])

            # Chunking
            chunks = create_chunks(P['text'])

            # Embeddings
            chunk_data = create_embeddings(chunks)
            P['chunks'] = chunk_data

            # Build FAISS Index
            store = VectorStore()
            store.build_index(chunk_data)
            P['store'] = store

            # Summary
            P['summary'] = hierarchical_summary(P['chunks'])

            # Keywords
            P['keywords'] = extract_keywords(P['chunks'], P['summary'])

            processed_papers.append(P)
        
        except Exception as e:

            print(f"Failed processing {P.get('title','Unknown')}")
            print(e)

    return processed_papers

# Selection Layer

def list_papers(papers: list[dict]) -> list[dict]:

    display = []

    for i, paper in enumerate(papers):

        display.append({
            "id" : i+1,
            "title" : paper.get('title', 'Unknown'),
            "authors" : ", ".join(paper.get('authors', [])),
            "published" : str(paper.get('published', 'Unknown')),
            "abstract" : paper.get('abstract', "")[:300] + "...",
        })

    return display

def select_paper(index: int, papers: list[dict]) -> dict | None:

    if index < 1 or index > len(papers):
        return None

    return papers[index-1]
    
    
class PaperSession:
    """
    Lifecycle of a paper in the session:
        1. select_paper() -> stores metadata (title, pdf_url, etc)
        2. process_text() -> downloads PDF, extracts and cleans text 
        3. process_index() -> chunks text, embeds, builds FAISS index
        4. ask()           -> retrieval + QA or generation (needs step 3)
        5. _get_analysis   -> summary + keywords extractor (lazily, cached)
    """

    def __init__(self):
        self.current_paper = None # To store system state
        self.store = None         # VectorStore lives here during a session
        self._analysis = None
        self._lc_analysis = None
        self._rag_chain = None
    
    # ── Stage 1: Select ───────────────────────────────────────────────────────
    def select_paper(self, paper: dict) -> dict:
        self.current_paper = paper
        self.store = None
        self._summary = None
        self._keywords = None
        self._analysis = None
        self._lc_analysis = None
        self._rag_chain = None

        return {
            "status" : "selected",
            "title" : paper.get('title', 'Unknown paper')
        }
    
    # ── Stage 2: Download + preprocess ────────────────────────────────────────

    def process_text(self) -> dict:
        if not self.current_paper:
            return {"error" : "No paper selected."}

        pdf_path = download_pdf_from_metadata(self.current_paper)
        if not pdf_path:
            return {"error" : "PDF download failed."}

        self.current_paper["pdf_path"] = pdf_path
        self.current_paper["text"] = preprocess_paper(pdf_path)

        return {
            "status" : "ok",
            "characters" : len(self.current_paper["text"]),
        }

    # ── Stage 3: Chunk + embed + FAISS ────────────────────────────────────────

    def process_index(self) -> dict:
        if not self.current_paper:
            return {"error" : "No paper selected."}
        if not self.current_paper.get("text"):
            return {"error": "Text not extracted yet. Call /process/text first."}

        chunks = create_chunks(self.current_paper["text"])
        chunk_data = create_embeddings(chunks)

        self.current_paper["chunks"] = chunk_data

        self.store = VectorStore()
        self.store.build_index(chunk_data)

        return {
            "status" : "ok",
            "chunks" : len(chunk_data),
        }

    def has_paper(self) -> bool:
        return self.current_paper is not None

    def is_ready(self) -> bool:
        return self.store is not None
     
    # ── Unified analysis (lazy, cached) ───────────────────────────────────────

    def _get_analysis(self) -> dict:
        """
        Internal method: computes analysis on first call, returns cache after.
        """ 

        if not self.current_paper:
            return {}

        if not self.current_paper.get("chunks"):
            return {}

        if self._analysis is None:
            print("[Session] Running paper analysis (first request)...")
            self._analysis = analyzer.analyze(self.current_paper)
        
        return self._analysis
    
    def get_analysis(self) -> dict:
        """
        Returns the full analysis dict.
        Used by /analysis endpoint.
        """
        return self._get_analysis()

    def get_lc_analysis(self) -> dict:
        """
        Langchain + Pydantic version of get_analysis()
        """
        if not self.current_paper or not self.current_paper.get("chunks"):
            return {}
        
        if self._lc_analysis is None:
            print("[Session] Running Langchain paper analysis (first request)...")
            self._lc_analysis = lc_analyze(self.current_paper)
        
        return self._lc_analysis

    def get_summary(self) -> str:
        return self._get_analysis().get("summary", "No summary available.")

    def get_keywords(self) -> list[dict]:
        keywords = self._get_analysis().get("keywords", [])
        return [{"keyword": k, "score":1.0} for k in keywords]

    def get_contributions(self) -> str:
        return self._get_analysis().get("contribution", "")
    
    def get_domain(self) -> str:
        return self._get_analysis().get("contribution", "")
    
    def _get_rag_chain(self):
        """
        Builds the LangChain RAG chain once and caches it for the session.
        """

        if self._rag_chain is None:
            self._rag_chain = build_rag_chain(self.store, top_k=5)
        return self._rag_chain



    # ── Q&A ───────────────────────────────────────────────────────────────────    
    def ask(self, question:str, mode:str = "generative") -> dict:
        if not self.current_paper:
            return {"error" : "No paper selected."}
        
        if not self.is_ready():
            return {"error": "Paper is still processing. Please wait."}

        relevant_chunks = self.store.search(question, top_k=5)


        if mode == "generative_lc":
            answer_text = lc_generate(question, relevant_chunks)

            answer = {
                "answer":           answer_text,
                "mode":             "generative_lc",
                "model":            f"{GROQ_MODEL} (via langchain)",
                "confidence_level": "N/A",
                "chunks_used":      len(relevant_chunks),
                "retrieved_chunks": relevant_chunks,
            }

        elif mode == "extractive":
            answer = answer_question(question, relevant_chunks)

            if answer is None:
                return {
                "answer":"No precise answer found.",
                "confidence_level":"Low"
            }

            answer["mode"] = "extractive"
            answer["retrieved_chunks"] = relevant_chunks     # <- for source viewer
        
        elif mode == "rag_lc":
            rag_chain = self._get_rag_chain()
            answer_text = rag_chain.invoke(question)

            answer = {
                "answer"            : answer_text,
                "mode"              : "rag_lc",
                "model"             : f"{GROQ_MODEL} (LangChain RAG chain)",
                "confidence_level"  : "N/A",
                "retrieved_chunks"  : [],
                "chunks_used"       : 5,
            }
        
        else:
            prompt = build_prompt(question, relevant_chunks)
            answer_text = generate_answer(prompt)

            answer = {
                "answer": answer_text,
                "mode": "generative",
                "model": GROQ_MODEL,
                "confidence_level" : "N/A",
                "chunks_used": len(relevant_chunks),
            }
        
        answer['paper_title'] = self.current_paper.get('title', 'Unknown Paper')
        answer['paper_authors'] = ", ".join(self.current_paper.get('authors', ['Unknown Authors']))
        published = self.current_paper.get('published')
        answer['paper_year'] = getattr(published, 'year', 'Unknown Year')

        return answer
    
    def get_metadata(self) -> dict:

        if not self.current_paper:
            return {}
        
        published = self.current_paper.get('published')

        year = getattr(published,'year','Unknown')

        return {
            "title" : self.current_paper.get('title', 'Unknown'),
            "authors" : ", ".join(self.current_paper.get('authors', ['Unknown'])),
            "year" : year,
            "abstract" : self.current_paper.get('abstract', "")
        }