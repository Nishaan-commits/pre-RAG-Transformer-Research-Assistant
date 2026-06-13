# Decision Log 

## Decision #1 : Initial Research Assistant Pipeline

### Approach

Initially avoided high-level RAG frameworks and focused on implementing the core pipeline manually to understand how modern NLP and retrieval systems work internally.

The first stages involved:
- fetching research papers using the arXiv library,
- extracting text from PDFs,
- applying NLP preprocessing techniques,
- chunking large documents into smaller contexts,
- converting chunks into embeddings for semantic retrieval.

For downstream NLP tasks such as:
- question answering,
- summarization,
- keyword extraction,

used transformer models from Hugging Face directly instead of relying on orchestration frameworks.

### Why

The goal was to build conceptual clarity around:
- text preprocessing,
- embeddings,
- semantic search,
- retrieval pipelines,
- transformer inference workflows.

Wanted to understand the lower-level mechanics before introducing abstraction layers.

### Tradeoffs

#### Advantages
- Strong understanding of the end-to-end NLP pipeline.
- Better understanding of how retrieval and embeddings actually work.
- Easier to reason about RAG architecture later.

#### Limitations
- Development speed was slower.
- Managing multiple transformer pipelines manually became complex.
- Inference latency was higher during local execution.
- Scaling the system became harder without optimized infrastructure.

### Current Improvements

To improve retrieval and inference performance:
- introduced a vector database for faster semantic retrieval,
- integrated Groq inference for lower-latency question answering.

These changes improved responsiveness and reduced the overhead of running multiple local transformer pipelines.



## Decision #2 : Staged Processing Pipeline and Lazy Analysis

### Approach

Initially, the application processed papers through a single workflow after search.

The flow involved:

- retrieving paper metadata,
- downloading PDFs,
- extracting text,
- chunking documents,
- generating embeddings,
- building the retrieval index,
- generating summaries and keywords.

This meant expensive processing was performed before the user had decided which paper they actually wanted to explore.

The pipeline was later refactored into staged processing:

- search returns metadata only,
- PDF download and text extraction occur after paper selection,
- indexing is performed as a separate step,
- summaries and keywords are generated only when requested.

### Why

The goal was to improve responsiveness and reduce unnecessary computation.

Many papers returned during search are never opened by the user, making immediate downloading and processing wasteful.

Similarly, many users only interact with the Q&A system and never use summaries or keywords.

Separating processing stages allows compute resources to be spent only when a feature is actually needed.

### Tradeoffs

#### Advantages

- Significantly faster search experience.
- Reduced unnecessary PDF processing.
- Lower inference and compute costs.
- Clear separation between search, processing, and analysis stages.
- More scalable architecture as the number of papers grows.

#### Limitations

- More API endpoints and state management.
- Additional complexity in the processing workflow.
- First-time summary generation introduces a small delay.

### Current Improvements

The refactor introduced several improvements:

- metadata retrieval is separated from paper processing,
- indexing occurs only after a paper is selected,
- summaries and keywords are generated lazily and cached,
- retrieved context chunks are exposed to the user,
- answers can reference source chunks for better transparency.

These changes improved both application responsiveness and explainability.


## Decision #3: Unified Paper Analysis Pipeline

### Approach

Initially, paper analysis was handled by two independent components:

- `summarizer.py` generated paper summaries,
- `keyword_extractor.py` generated keywords.

Each component performed its own processing and inference workflow, while the frontend requested summary and keywords separately.

The analysis pipeline was later consolidated into a single component:

- `paper_analyzer.py` performs one LLM call,
- returns structured JSON output,
- generates summary, keywords, contribution, and domain together,
- caches the result for future requests.

The previous `_summary` and `_keywords` caches were replaced with a single `_analysis` cache.

### Why

The goal was to reduce redundant inference and create a richer understanding of each paper.

Summary generation and keyword extraction both require understanding the same document context. Running separate analysis pipelines duplicated work and increased latency.

A single structured analysis allows one model call to generate multiple insights while maintaining consistency between outputs.

### Tradeoffs

#### Advantages

- Reduced number of LLM calls.
- Lower inference cost and latency.
- Consistent outputs generated from the same context.
- Simpler caching strategy.
- Easier to extend with additional analysis fields.

#### Limitations

- Larger prompt and response payload.
- More reliance on structured JSON generation.
- A failure in analysis affects all derived outputs simultaneously.

### Current Improvements

The new analysis pipeline now provides:

- paper summary,
- extracted keywords,
- research contribution,
- domain classification.

Analysis results are generated once and cached for reuse across endpoints.

Existing frontend contracts were preserved:

- `get_summary()` still returns a plain string,
- `get_keywords()` still returns a keyword list structure,

allowing the frontend to remain compatible while benefiting from the new architecture.

## Decision #4: LangChain Integration Through Progressive Abstraction

### Approach

Initially, the entire retrieval and generation pipeline was implemented manually.

This included:

- chunk retrieval from the vector store,
- prompt construction,
- Groq API interaction,
- response parsing,
- answer generation.

After understanding the complete pipeline, LangChain components were introduced incrementally rather than replacing the existing system.

The integration occurred in stages:

- ChatPromptTemplate for prompt management,
- ChatGroq for model interaction,
- PydanticOutputParser for structured outputs,
- BaseRetriever wrapper around the existing FAISS vector store,
- a full LCEL RAG chain combining retrieval and generation.

The original manual pipeline was preserved alongside the LangChain implementation to allow direct comparison between approaches.

### Why

The goal was to learn LangChain as an orchestration framework without losing understanding of the underlying retrieval and generation mechanics.

Implementing the system manually first made it easier to understand what LangChain abstractions were actually doing internally.

By introducing components gradually, each abstraction could be evaluated independently rather than treating LangChain as a black box.

### Tradeoffs

#### Advantages

- Better understanding of both manual and framework-based RAG systems.
- Cleaner composition of retrieval and generation workflows.
- Reduced boilerplate for prompt handling and model interaction.
- Easier extensibility through reusable chain components.
- Exposure to industry-standard GenAI tooling.

#### Limitations

- Additional dependency on a framework.
- Increased abstraction can hide implementation details.
- Debugging may require understanding both LangChain internals and custom code.
- Some workflows become less explicit than manual implementations.

### Current Improvements

The integration introduced several capabilities:

- ChatPromptTemplate-based prompt construction,
- ChatGroq model integration,
- structured output parsing with Pydantic,
- VectorStoreRetriever adapter for the existing FAISS index,
- full retrieval-augmented generation chains using LCEL.

The application now supports multiple answering strategies:

- Extractive QA,
- Manual Generative QA,
- LangChain LLM Generation,
- LangChain RAG.

This allows direct comparison between manual and framework-based approaches within the same application.

