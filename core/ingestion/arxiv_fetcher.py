import arxiv 
import requests 
import os
import time
from config import PAPERS_DIR


def extract_metadata(result):

    return {
        "paper_id" : result.get_short_id(),
        "title" : result.title,
        "abstract" : result.summary, 
        "authors" : [b.name for b in result.authors],
        "published" : result.published.date(),
        "pdf_url" : result.pdf_url,
        "categories" : result.categories,
    }

def download_pdf_from_metadata(paper: dict , folder = PAPERS_DIR) -> str | None:

    try: 
        os.makedirs(folder, exist_ok=True)

        safe_id = paper["paper_id"].replace("/", "_")
        filename = safe_id + ".pdf"

        path = os.path.join(folder, filename)

        if os.path.exists(path):
            print(f"[Fetcher] PDF already cached: {filename}")
            return path 

        response = requests.get(paper["pdf_url"], stream=True, timeout=30)

        response.raise_for_status()

        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return path

    except Exception as e:

        print("Download failed :", e)
        return None


def search_papers(query: str, max_results : int = 5) -> list[dict]:

    client = arxiv.Client(
    page_size=max_results,
    delay_seconds=5.0,
    num_retries=3
    )

    papers = []

    for attempt in range(3):
        try :
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )
            for R in client.results(search):
                papers.append(extract_metadata(R))
                
            break # success, exit
        except arxiv.HTTPError as e:
            if e.status == 429:
                wait = (attempt + 1) * 10 # 10s, 20s, 30s
                print(f"Rate limited, Waiting {wait}s before retry......")
                time.sleep(wait)
            else:
                raise # re-raise non-429 errors
            
    return papers 



        


