from utils.arxiv_fetcher import *
from nlp.preprocessing import *
from nlp.chunker import *
from models.embedding import *
from nlp.Keyword_extractor import *
from models.QA_model import *
from nlp.summarizer import *

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

def list_papers(papers):

    display = []

    for i, paper in enumerate(papers):

        display.append({
            "id" : i+1,
            "title" : paper.get('title', 'Unknown'),
            "authors" : ", ".join(paper.get('authors', [])),
            "published" : paper.get('published', 'Unknown'),
            "chunks" : len(paper.get('chunks', []))
        })

    return display

def select_paper(index, papers):

    if index < 1 or index > len(papers):
        return None

    return papers[index-1]
    
    
class PaperSession:

    def __init__(self):
        self.current_paper = None # To store system state
    
    def load_paper(self, paper):
        self.current_paper = paper

        return {
            "status" : "Paper Loaded",
            "title" : paper.get('title', 'Unknown paper')
        }
    
    def has_paper(self):
        return self.current_paper is not None
     
    def ask(self, question):
        if self.current_paper is None:
            return {
                "error" : "No paper selected"
                }
        
        answer = answer_question(
            question,
            self.current_paper.get('chunks', [])
        )

        if answer is None:
            return {
            "answer":"No precise answer found.",
            "confidence_level":"Low"
        }
        
        answer['paper_title'] = self.current_paper.get('title', 'Unknown Paper')
        answer['paper_authors'] = ", ".join(self.current_paper.get('authors', ['Unknown Authors']))
        published = self.current_paper.get('published')
        answer['paper_year'] = getattr(published, 'year', 'Unknown Year')

        return answer

    def get_summary(self):

        if not self.current_paper:
            return {
                "summary" : "No paper Loaded"
            }
        
        return self.current_paper.get('summary')
    
    def get_keywords(self):

        if not self.current_paper:
            return []
        
        return self.current_paper.get('keywords', [])
    
    def get_metadata(self):

        if not self.current_paper:
            return {}
        
        published = self.current_paper.get('published')

        year = getattr(published,'year','Unknown')

        return {
            "title" : self.current_paper.get('title', 'Unknown Paper'),
            "authors" : ", ".join(self.current_paper.get('authors', ['Unknown Authors'])),
            "year" : year,
            "keywords" : self.current_paper.get('keywords', [])
        }