# Cosine Similarity 
from models.embedding import embedding_model
from transformers import pipeline
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from config import QA_MODEL_PATH, QA_MODEL_NAME 
import os

def load_qa_model():
  if os.path.isdir(QA_MODEL_PATH):
      qa_model = pipeline(
          "question-answering",
          model=QA_MODEL_PATH,
          tokenizer=QA_MODEL_PATH,
          local_files_only=True
      )
  else:
      print("Downloading QA model from HuggingFace...")
      qa_model = pipeline(
          "question-answering",
          model=QA_MODEL_NAME
      )
      # Optional: save locally
      qa_model.model.save_pretrained(QA_MODEL_PATH)
      qa_model.tokenizer.save_pretrained(QA_MODEL_PATH)
  
  return qa_model


def semantic_search(question, paper_chunks, model):
  question_embedding = model.encode(question, normalize_embeddings=True)

  chunk_texts = []
  chunk_embeddings = []
  for chunk, emb in paper_chunks:
    chunk_texts.append(chunk)
    chunk_embeddings.append(emb)

  similarities = cosine_similarity([question_embedding], chunk_embeddings)[0]
  top_k = 3
  top_indices = np.argsort(similarities)[-top_k:][::-1]

  return [(chunk_texts[i], similarities[i]) for i in top_indices]

# QA Model

from sklearn.preprocessing import normalize

qa_model = load_qa_model()

def answer_question(question, chunks):
  answers = []
  top_chunks = semantic_search(question, chunks, embedding_model)

  for chunk_text, similarity in top_chunks:
    output = qa_model(question=question, context=chunk_text)

    # Penalize very short answers
    if len(output["answer"].split()) < 2:
      continue

    # QA score -> 0 to 1 but similarity -> -1 to 1
    norm_similarity = float((similarity + 1)/ 2) # Standard cosine normalization from -1 to 1 to 0 to 1
    combined_score = float(0.6 * output["score"] + 0.4 * norm_similarity)

    # If no answer -> prevent crash
    if output["answer"].strip() == "":
      continue

    # Answer Snippet
    start = output['start']
    end = output['end']
    context_snippet = chunk_text[max(0,start-50):min(len(chunk_text),end+50)]

    # Confidence Level
    if combined_score > 0.6:
      confidence = "High"
    elif combined_score > 0.4:
      confidence = "Medium"
    else: 
      confidence = "Low"

    answers.append({
        "answer": output["answer"],
        "qa_score": float(output["score"]),
        "similarity_score": float(similarity),
        "final_score": combined_score,
        "source": chunk_text[:500],
        "context_snippet": context_snippet,
        "confidence_level": confidence
    })

  # If empty answers prevent crash
  if not answers: 

    best_chunk = top_chunks[0][0]
    return {
        "answer" : "No precise answer found. Showing most relevant context",
        "context_snippet" : best_chunk[:300],
        "confidence_level" : "low"
    }
  best_answer = max(answers, key=lambda x : x["final_score"])

  return best_answer