
import arxiv
from fastapi import FastAPI, HTTPException
from backend.paper_assistant import PaperSession, fetch_papers, list_papers, select_paper

app = FastAPI()
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


@app.get("/analysis")
def get_analysis():
    """
    Returns full structured analysis in one request.
    """
    analysis = session.get_analysis()
    if not analysis:
        raise HTTPException(status_code=400, detaik="Paper not ready for analysis.")
    return analysis

@app.get("/summary")
def get_summary():
    return {
        "summary" : session.get_summary()
    }


@app.get("/keywords")
def get_keywords():
    return {
        "keywords" : session.get_keywords()
    }

@app.get("/contribution")
def get_contribution():
    return {"contribution": session.get_contribution()}

@app.get("/domain")
def get_domain():
    return {"domain": session.get_domain()}

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