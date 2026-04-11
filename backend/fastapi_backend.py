from fastapi import FastAPI
from backend.paper_assistant import *

app = FastAPI()
session = PaperSession()

papers_cache = []

@app.post("/search")
def search_paper(query:str, max_results:int=5):
    global papers_cache

    try:
        papers_cache = process_paper(query, max_results)
        return list_papers(papers_cache)
    except arxiv.HTTPError as e:
        if e.status == 429:
            raise HTTPException(
                status_code=429,
                detail="arXiv is rate limiting us. Please wait a moment and try again."
            )
        raise HTTPException(status_code=502, detail=f"arXiv API error: {str(e)}")
    except BaseException as e:
        raise HTTPException(status_code=500, detail=str(e))
        

@app.post("/select")
def choose_paper(paper_id:int):
    global papers_cache

    result = select_paper(paper_id, papers_cache)

    if not result:
        return {"error": "Invalid paper"}
    
    session.load_paper(result)

    return session.get_metadata()

@app.post("/ask")
def ask_question(question:str):
    
    return session.ask(question)


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


@app.get("/metadata")
def get_metadata():
    return session.get_metadata()

