# 🔍 Pre-RAG Transformer Research Assistant

An AI-powered research paper assistant that retrieves, analyzes, and answers questions from arXiv papers using **Transformer models and semantic search** — built *from scratch without RAG frameworks*.

---

## 📌 Overview

This project implements a **pre-RAG (Retrieval-Augmented Generation) pipeline** using classical NLP and transformer-based techniques.

Instead of relying on LLM orchestration frameworks, it builds the full system manually:

* PDF ingestion → chunking → embeddings → retrieval → QA
* Designed to simulate how **real-world RAG systems work internally**

---

## ✨ Key Features

* 🔎 **ArXiv Paper Search**
  Fetch and process research papers dynamically

* 🧠 **Semantic Search (Embeddings)**
  Retrieve the most relevant chunks using cosine similarity

* ❓ **Question Answering System**
  Extract answers from papers using transformer QA models

* 📝 **Hierarchical Summarization**
  Multi-stage summarization for long documents

* 🏷️ **Keyword Extraction (KeyBERT)**
  Identify core topics and concepts from papers

* 📊 **Explainable Outputs**
  Includes confidence scores, similarity scores, and context snippets

---

## 🧱 System Architecture

```
ArXiv PDF
   ↓
Text Extraction
   ↓
Chunking (token-based)
   ↓
Embeddings (Sentence Transformers)
   ↓
Semantic Retrieval
   ↓
QA / Summarization / Keywords
   ↓
FastAPI Backend
   ↓
Streamlit UI
```

---

## 🛠️ Tech Stack

* **Backend:** FastAPI
* **Frontend:** Streamlit
* **ML/NLP:**

  * HuggingFace Transformers
  * Sentence-Transformers
  * KeyBERT
* **Core Concepts:**

  * Embeddings & cosine similarity
  * Extractive QA
  * Hierarchical summarization
  * Retrieval pipelines

---

## ⚙️ How It Works

1. User searches for a paper
2. System downloads and processes the PDF
3. Text is split into semantic chunks
4. Each chunk is embedded into vector space
5. On query:

   * Relevant chunks are retrieved
   * QA model extracts the answer
   * Best answer is ranked using hybrid scoring

---

## 🚀 Run Locally

### 1. Install dependencies

```
pip install -r requirements.txt
```

### 2. Start FastAPI backend

```
uvicorn backend.fastapi_backend:app --reload
```

### 3. Launch Streamlit UI

```
streamlit run app/app.py
```

---

## 📈 Example Use Cases

* Quickly understand research papers
* Extract key insights without reading full PDFs
* Explore academic topics interactively
* Build intuition for RAG systems

---

## 🔮 Future Improvements (Phase 2)

* Vector database integration (FAISS / Chroma)
* Full RAG with LLM answer synthesis
* Multi-paper comparison
* Research gap detection
* Agent-based workflows

---

## 💡 Key Learning Outcomes

* Built a full **retrieval-based QA system from scratch**
* Understood internal mechanics of RAG pipelines
* Applied transformer models in real-world NLP workflows
* Designed modular ML system architecture

---

## 👤 Author

Mohd. Nishaan

---

## ⭐ Why This Project Stands Out

Unlike typical GenAI projects that rely on frameworks, this project:

* Implements **core RAG concepts manually**
* Focuses on **understanding over abstraction**
* Demonstrates **ML + backend engineering integration**

---

If you found this useful, feel free to ⭐ the repo!

