import os 
from transformers import pipeline, AutoTokenizer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_STORE = os.path.join(BASE_DIR, "model_store")

QA_MODEL_PATH = os.path.join(MODEL_STORE, "roberta-base-squad2")
EMBED_MODEL_PATH = os.path.join(MODEL_STORE, "all-MiniLM-L6-v2")
SUMMARIZER_MODEL_PATH = os.path.join(MODEL_STORE, "distilbart-cnn-12-6")

SUMMARIZER_MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
QA_MODEL_NAME = "deepset/roberta-base-squad2"

DATA_DIR = os.path.join(BASE_DIR, "data")
PAPERS_DIR = os.path.join(DATA_DIR, "papers")

FAISS_INDEX_DIR = os.path.join(DATA_DIR, "faiss_indexes")
FAISS_INDEX_FILE = "index.faiss"
FAISS_CHUNKS_FILE = "chunks.pkl"

GROQ_MODEL = "llama-3.3-70b-versatile"