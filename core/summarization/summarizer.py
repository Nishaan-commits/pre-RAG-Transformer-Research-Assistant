from transformers import pipeline
from sklearn.preprocessing import normalize
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from config import SUMMARIZER_MODEL_PATH, SUMMARIZER_MODEL_NAME
import os

def load_summarizer():

    if os.path.isdir(SUMMARIZER_MODEL_PATH):

        print("Loading summarizer locally")

        summarizer = pipeline(
            "summarization",
            model=SUMMARIZER_MODEL_PATH,
            tokenizer=SUMMARIZER_MODEL_PATH
        )

    else:

        print("Downloading summarizer")

        summarizer = pipeline(
            "summarization",
            model=SUMMARIZER_MODEL_NAME
        )

        summarizer.model.save_pretrained(
            SUMMARIZER_MODEL_PATH
        )

        summarizer.tokenizer.save_pretrained(
            SUMMARIZER_MODEL_PATH
        )

    return summarizer

summarizer = load_summarizer()

def Top_chunks(chunks):
    if len(chunks) <= 12:
        top_k = max(4, len(chunks)//2)
    else:
        top_k = 8

    chunk_embeddings = []
    chunk_texts = []

    for chunk, emb in chunks:
      chunk_embeddings.append(emb)
      chunk_texts.append(chunk)

    chunk_embeddings = np.array(chunk_embeddings)
    
    # Paper representation
    paper_embedding = np.mean(chunk_embeddings, axis=0)

    # Normalize - improves retrieval quality
    chunk_embeddings = normalize(chunk_embeddings)
    paper_embedding = normalize([paper_embedding])[0]

    # Similarity Ranking
    similarities = cosine_similarity([paper_embedding], chunk_embeddings)[0]
    top_indices = np.argsort(similarities)[::-1][:top_k]

    top_chunks =  [chunk_texts[i] for i in top_indices]

    return top_chunks

def hierarchical_summary(chunks):
    top_chunks = Top_chunks(chunks)

    # Chunk Cleanup

    # First Step Summaries
    chunk_summaries = []

    for chunk_text in top_chunks:

        summary = summarizer(
            chunk_text,
            max_length=200,
            min_length=100,
            truncation=True,
            do_sample=False
        )[0]["summary_text"]

        chunk_summaries.append(summary)

    # Combine Summaries
    combined_text = "\n".join(chunk_summaries)

    # Second Stage Summary
    final_summary = summarizer(
        combined_text,
        max_length=300,
        min_length=100,
        truncation=True,
        do_sample=False
    )[0]["summary_text"]

    return final_summary