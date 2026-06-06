
from keybert import KeyBERT
from core.summarization.summarizer import Top_chunks
from core.retrieval.embedding import embedding_model

kw_model = KeyBERT(model=embedding_model)

def extract_keywords(chunks, summary):

  top_chunks = Top_chunks(chunks)
  text = summary + "\n" + "\n".join(top_chunks)

  keywords = kw_model.extract_keywords(
      text, 
      keyphrase_ngram_range=(1,3),
      stop_words = 'english',
      use_mmr = True,
      diversity = 0.7,
      nr_candidates=20,
      top_n = 12
  )

  # Remove generic ones
  clean_keywords = []

  for k,s in keywords:

    if len(k) < 4:
        continue

    if k.lower() in ["paper","model","method","results","approach",
    "study","work","analysis"]:
        continue

    clean_keywords.append((k,s))

  # sort by length (longer phrases first)
  clean_keywords.sort(key=lambda x: len(x[0]), reverse=True)
  
  final_keywords = []
  
  for kw, score in clean_keywords:
  
      kw_lower = kw.lower()
  
      # check if already covered by longer keyword
      if any(kw_lower in existing.lower() for existing, _ in final_keywords):
          continue
  
      final_keywords.append((kw, score))

  return [
  {
  "keyword":k,
  "score":float(s)
  }
  for k,s in final_keywords[:8]
  ]