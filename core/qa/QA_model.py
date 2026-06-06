"""

Responsibility: Given a question and a list of relevant chunk texts,
                find and return the best answer.

"""

from transformers import pipeline
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


# QA Model
qa_model = load_qa_model()

def answer_question(question: str, chunks: list[str]) -> dict:
  """

  Extracts the best answer to a question from pre-retrieved chunks.

  """
  
  if not chunks:
    return {
      "answer" : "No relevant context found.",
      "confidence_level" : "low"
    }
  
  answers = []

  for chunk_text in chunks:
    output = qa_model(question=question, context=chunk_text)

    # Penalize very short answers
    if len(output["answer"].split()) < 2:
      continue

    # If no answer -> prevent crash
    if output["answer"].strip() == "":
      continue

    qa_score = float(output["score"])

    # Answer Snippet
    start = output['start']
    end = output['end']
    context_snippet = chunk_text[max(0,start-50):min(len(chunk_text),end+50)]

    # Confidence Level
    if qa_score > 0.6:
      confidence = "High"
    elif qa_score > 0.4:
      confidence = "Medium"
    else: 
      confidence = "Low"

    answers.append({
        "answer": output["answer"],
        "final_score": qa_score,
        "source": chunk_text[:500],
        "context_snippet": context_snippet,
        "confidence_level": confidence
    })

  # If empty answers prevent crash
  if not answers: 
    return {
        "answer" : "No precise answer found. Showing most relevant context",
        "context_snippet" : chunks[0][:300],
        "confidence_level" : "low"
    }
  best_answer = max(answers, key=lambda x : x["final_score"])

  return best_answer