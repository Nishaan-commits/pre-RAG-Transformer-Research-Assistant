"""
api.py — DEMO BRANCH
 
Endpoints kept:
  POST /search          metadata only, fast
  POST /select          pick a paper
  POST /process/text    download + preprocess
  POST /process/index   chunk + embed + FAISS
  POST /ask             mode=generative or mode=rag_lc
  GET  /metadata        paper info
  GET  /status          is the paper ready?
 
Removed:
  /analysis, /summary, /keywords, /contribution, /domain, /ask/lc
"""


import arxiv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.paper_assistant import PaperSession, fetch_papers, list_papers, select_paper

app = FastAPI(title="Research Paper Assistant - Demo")
# Allow Streamlit (different port/domain) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

session = PaperSession()
papers_cache = []

@app.post("/search")
def search(query:str, max_results:int=5):
    global papers_cache

    try:
        papers_cache = fetch_papers(query, max_results)
        return list_papers(papers_cache)

    except arxiv.HTTPError as e:
        if e.status == 429:
            raise HTTPException(
                status_code=429,
                detail="arXiv is rate limiting us. Please wait a moment and try again."
            )
        raise HTTPException(status_code=502, detail=f"arXiv API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        

@app.post("/select")
def choose_paper(paper_id:int):

    paper = select_paper(paper_id, papers_cache)

    if not paper:
        return HTTPException(status_code=404, detail = "Invalid paper ID.")

    return session.select_paper(paper)

@app.post("/process/text")
def process_text():
    """
    Download PDF + extract clean text.
    """

    result = session.process_text()
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/process/index")
def process_index():
    """
    chunk + embed + build FAISS index.
    Necessary for /ask to work.
    """
    result = session.process_index()
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result 

@app.post("/ask")
def ask_question(question:str, mode : str = "generative"):
    
    return session.ask(question, mode)

@app.get("/metadata")
def get_metadata():
    return session.get_metadata()

@app.get("/status")
def get_status():
    
    return {
        "has_paper" : session.has_paper(),
        "is_ready" : session.is_ready(),
        "title" : session.current_paper.get("title") if session.current_paper else None,
    }