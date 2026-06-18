import os
import streamlit as st
import requests

# API_URL comes from environment variable on Render.
# Falls back to localhost for local development.
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Research Paper Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

/* ── Root variables ── */
:root {
    --bg-base:      #07111f;
    --bg-surface:   #0d1e30;
    --bg-card:      #112030;
    --bg-input:     #0a1929;
    --accent:       #4fc3f7;
    --accent-warm:  #f4a94e;
    --accent-green: #56cfb2;
    --border:       rgba(79, 195, 247, 0.15);
    --border-warm:  rgba(244, 169, 78, 0.25);
    --text-primary: #e8f4fd;
    --text-secondary:#8bafc9;
    --text-muted:   #4a6f8a;
    --glow:         rgba(79, 195, 247, 0.08);
}

/* ── Base reset ── */
html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    color: var(--text-primary);
}

.stApp {
    background: var(--bg-base);
    background-image:
        radial-gradient(ellipse 80% 60% at 10% 0%, rgba(19,54,87,0.55) 0%, transparent 65%),
        radial-gradient(ellipse 60% 40% at 90% 100%, rgba(13,40,65,0.45) 0%, transparent 60%),
        url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%234fc3f7' fill-opacity='0.025'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--bg-surface) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"]::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent), var(--accent-warm));
}

/* ── Main header ── */
.main-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 28px 0 18px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 28px;
}

.main-header .icon {
    font-size: 2.4rem;
    filter: drop-shadow(0 0 12px var(--accent));
}

.main-header h1 {
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, var(--accent) 0%, #90caf9 60%, var(--accent-warm) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    line-height: 1.2;
}

.main-header p {
    color: var(--text-secondary);
    font-size: 0.85rem;
    font-weight: 300;
    margin: 2px 0 0;
    letter-spacing: 0.5px;
}

/* ── Section labels ── */
.section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.section-label::after {
    content: "";
    flex: 1;
    height: 1px;
    background: var(--border);
}

/* ── Cards ── */
.paper-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
    transition: border-color 0.2s, box-shadow 0.2s;
    position: relative;
    overflow: hidden;
}

.paper-card::before {
    content: "";
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    background: linear-gradient(180deg, var(--accent), var(--accent-warm));
    border-radius: 3px 0 0 3px;
}

.paper-card:hover {
    border-color: rgba(79, 195, 247, 0.35);
    box-shadow: 0 0 20px var(--glow);
}

.paper-id {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: var(--accent);
    background: rgba(79,195,247,0.1);
    padding: 2px 8px;
    border-radius: 4px;
    display: inline-block;
    margin-bottom: 6px;
}

.paper-title {
    font-size: 0.9rem;
    color: var(--text-primary);
    font-weight: 500;
    line-height: 1.4;
}

/* ── Info panels ── */
.info-panel {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px 22px;
    margin-bottom: 16px;
}

.info-panel h4 {
    font-family: 'Playfair Display', serif;
    font-size: 1rem;
    color: var(--accent-warm);
    margin: 0 0 10px;
}

.info-panel p {
    color: var(--text-secondary);
    font-size: 0.88rem;
    line-height: 1.7;
    margin: 0;
}

/* ── Keyword chips ── */
.keyword-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 14px 0 4px;
}

.chip {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    padding: 4px 12px;
    border-radius: 20px;
    border: 1px solid rgba(86, 207, 178, 0.3);
    background: rgba(86, 207, 178, 0.08);
    color: var(--accent-green);
    letter-spacing: 0.3px;
}

/* ── Sidebar QA panel ── */
.sidebar-header {
    font-family: 'Playfair Display', serif;
    font-size: 1.15rem;
    color: var(--text-primary);
    margin-bottom: 4px;
}

.sidebar-subtext {
    font-size: 0.78rem;
    color: var(--text-muted);
    margin-bottom: 20px;
    line-height: 1.5;
}

.answer-block {
    background: rgba(10, 25, 41, 0.8);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 16px;
    margin-top: 12px;
}

.answer-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 5px;
}

.answer-label.ans   { color: var(--accent); }
.answer-label.conf  { color: var(--accent-warm); }
.answer-label.ctx   { color: var(--accent-green); }

.answer-text {
    font-size: 0.85rem;
    color: var(--text-secondary);
    line-height: 1.65;
}

/* ── Streamlit widget overrides ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    background: var(--bg-input) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
    border-radius: 8px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 0.88rem !important;
}

.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: rgba(79,195,247,0.5) !important;
    box-shadow: 0 0 0 2px rgba(79,195,247,0.1) !important;
}

.stTextInput label, .stNumberInput label {
    color: var(--text-secondary) !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
}

/* Primary buttons */
.stButton > button[kind="primary"],
.stButton > button {
    background: linear-gradient(135deg, #1565c0, #0d47a1) !important;
    color: #e8f4fd !important;
    border: 1px solid rgba(79,195,247,0.3) !important;
    border-radius: 8px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 0.83rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.3px !important;
    padding: 0.45rem 1.2rem !important;
    transition: all 0.2s !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #1976d2, #1565c0) !important;
    border-color: rgba(79,195,247,0.6) !important;
    box-shadow: 0 0 16px rgba(79,195,247,0.2) !important;
    transform: translateY(-1px) !important;
}

/* Divider */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 20px 0 !important;
}

/* Remove Streamlit branding */
#MainMenu, footer { visibility: hidden; }
.stDeployButton { display: none; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR — Q&A
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
        <div style="padding: 10px 0 6px;">
            <div class="sidebar-header">💬 Ask the Paper</div>
            <div class="sidebar-subtext">
                Load a paper first, then ask anything about its content,
                methodology, or findings.
            </div>
        </div>
    """, unsafe_allow_html=True)

    paper_loaded = st.session_state.get("loaded", False)

    if not paper_loaded:
        st.markdown("""
            <div style="
                background: rgba(79,195,247,0.05);
                border: 1px dashed rgba(79,195,247,0.2);
                border-radius: 8px;
                padding: 16px;
                text-align: center;
                color: #4a6f8a;
                font-size: 0.82rem;
                line-height: 1.6;
            ">
                🔭 No paper loaded yet.<br>Search and load one to start asking questions.
            </div>
        """, unsafe_allow_html=True)

    else:
        # ── Mode selector ─────────────────────────────────────────────────────
        # Placed above the input so the user picks their mode before asking.
        # st.radio returns the label string — we map it to the API param value.
        mode_label = st.radio(
            "Answer mode",
            options=["🧠 Generative (manual)", "🔗 LangChain RAG"],
            index=0,
            horizontal=True,
            help=(
                "Generative (manual): hand-built prompt + Groq.\n"
                "LangChain RAG: retrieval is inside the chain — full LC pipeline."
            )
        )
        # Map display label → API param value
        mode = "rag_lc" if "LangChain" in mode_label else "generative"

        # Mode explanation — helps demo viewers understand the difference
        if mode == "generative":
            st.markdown("""
                <div style="font-size:0.75rem;color:#4a6f8a;padding:8px 0 4px;line-height:1.5;">
                    Retrieval → Context → Prompt → Groq<br>
                    <span style="color:#2a5a7a;">Each step written by hand.</span>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="font-size:0.75rem;color:#4a6f8a;padding:8px 0 4px;line-height:1.5;">
                    VectorStoreRetriever | ChatPromptTemplate | ChatGroq<br>
                    <span style="color:#2a5a7a;">Retrieval is inside the chain.</span>
                </div>
            """, unsafe_allow_html=True)


        # ── Question input ────────────────────────────────────────────────────
        question = st.text_input(
            "Your question",
            placeholder="e.g. Frame questions that i can ask from this paper?",
            label_visibility="collapsed",
        )

        if st.button("Ask ›", use_container_width=True):
            if question.strip():
                with st.spinner("Querying paper…"):
                    try:
                        response = requests.post(
                            f"{API_URL}/ask",
                            params={"question": question, "mode": mode},  # ← mode passed here
                        )
                        st.session_state["last_answer"] = response.json()
                    except Exception as e:
                        st.error(f"Request failed: {e}")
            else:
                st.warning("Please enter a question.")

        # ── Answer display ────────────────────────────────────────────────────
        if "last_answer" in st.session_state:
            ans          = st.session_state["last_answer"]
            answer_mode  = ans.get("mode", "generative")
            badge_class = "mode-badge-lc" if answer_mode == "rag_lc" else "mode-badge-manual"

            st.markdown(f"""
                <div class="answer-block">
                    <div class="answer-label ans">Answer</div>
                    <div style="font-size:0.85rem;color:var(--text-secondary);
                                line-height:1.65;margin-bottom:10px;">
                        {ans.get('answer', '—')}
                    </div>
                    <span class="{badge_class}">{ans.get('model', '—')}</span>
                </div>
            """, unsafe_allow_html=True)

            
            # Source Viewer
            # Shows the exact chunks FAISS retrieved to answer this question.
            chunks = ans.get("retrieved_chunks", [])
            if chunks:
                with st.expander(f"📚 Retrieved Context — {len(chunks)} chunks", expanded=False):
                    for i, chunk in enumerate(chunks, 1):
                        preview = chunk[:400] + "..." if len(chunk) > 400 else chunk
                        st.markdown(f"""
                            <div class= "chunk-box">
                                <div class = "chunk-label">Chunk {i}</div>
                                {preview}
                            </div>
                        """, unsafe_allow_html=True)
            elif answer_mode == "rag_lc":
                st.caption("💡 Context is retrieved inside the LangChain chain.")


    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("""
        <div style="font-size:0.7rem; color:#2a4a62; text-align:center; padding-top:4px;">
            FAISS · SentenceTransformers · Groq · LangChain
        </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN PANEL
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
    <div class="main-header">
        <div class="icon">🔬</div>
        <div>
            <h1>Research Paper Assistant</h1>
            <p>Manual RAG · LangChain RAG · Powered by FAISS + Groq</p>
        </div>
    </div>
""", unsafe_allow_html=True)

col_search, col_btn = st.columns([5, 1])

with col_search:
    query = st.text_input(
        "Search",
        placeholder="e.g. transformer attention mechanisms, diffusion models…",
        label_visibility="collapsed",
    )

with col_btn:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    search_clicked = st.button("Search", use_container_width=True)

if search_clicked and query.strip():
    with st.spinner("Searching ArXiv…"):
        try:
            response = requests.post(f"{API_URL}/search", params={"query": query})
            st.session_state["papers"] = response.json()
            st.session_state["loaded"] = False
            st.session_state.pop("last_answer", None)
        except Exception as e:
            st.error(f"Search failed: {e}")

# ── Results ──
if "papers" in st.session_state and st.session_state["papers"]:
    papers = st.session_state["papers"]
    st.markdown(f"""
        <div class="section-label">
            Results &nbsp;·&nbsp; {len(papers)} paper{"s" if len(papers) != 1 else ""} found
        </div>
    """, unsafe_allow_html=True)

    for paper in papers:
        st.markdown(f"""
            <div class="paper-card">
                <div class="paper-id">#{paper['id']}</div>
                <div class="paper-title">{paper['title']}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Paper selector ──
    st.markdown('<div class="section-label">Load Paper</div>', unsafe_allow_html=True)

    col_id, col_load = st.columns([3, 1])
    with col_id:
        paper_id = st.number_input(
            "Paper ID",
            min_value=1,
            step=1,
            label_visibility="collapsed",
        )
    with col_load:
        load_clicked = st.button("Load Paper", use_container_width=True)

    if load_clicked:
        # Step 1: Select (instant - just metadata)
        sel = requests.post(f"{API_URL}/select", params={"paper_id" : int(paper_id)})
        if sel.status_code != 200:
            st.error(f"Could not select paper: {sel.json().get('detail', 'Unknown error')}")
        else:
            # Step 2 & 3: show reak progress as each stage completes
            # st.status is a Streamlit component that shows a collapsible 
            # progress container. Each st.write() inside it adds a stage line.
            # The stages are Real - each one is an actual API call completing.
            with st.status("⚙️ Processing paper...", expanded=True) as status:
                st.write("📥 Downloading PDF and extracting text...")
                r_text = requests.post(f"{API_URL}/process/text")
                if r_text.status_code != 200:
                    status.update(label = "❌ Text extraction failed", status="error")
                    st.error(r_text.json().get("detail", "Unknown error"))
                    st.stop()

                st.write("🧠 Generating embeddings and building search index...")
                r_index = requests.post(f"{API_URL}/process/index")
                if r_index.status_code != 200:  
                    status.update(label = "❌ Indexing failed", state="error")
                    st.error(r_index.json().get("detail", "Unknown error"))
                    st.stop()
                
                chunk_count = r_index.json().get("chunks", "?")
                st.write(f"✅ Ready - {chunk_count} chunks indexed")
                status.update(label = "Paper ready for questions!", state="complete", expanded=False)

            st.session_state["loaded"] = True
            st.session_state.pop("last_answer", None)
            st.rerun()


# ── Analysis ── (lazy - only on request)
if st.session_state.get("loaded"):
    try:
        meta = requests.get(f"{API_URL}/metadata").json()
        st.markdown(f"""
            <div style="margin-top:20px;padding:16px 20px;background:var(--bg-card);
                        border:1px solid var(--border);border-radius:10px;">
                <div style="font-family:'Playfair Display',serif;font-size:1rem;
                            color:var(--accent-warm);margin-bottom:6px;">
                    {meta.get('title', '')}
                </div>
                <div style="font-size:0.82rem;color:var(--text-muted);">
                    {meta.get('authors', '')} · {meta.get('year', '')}
                </div>
                <div style="font-size:0.82rem;color:var(--text-secondary);
                            margin-top:8px;line-height:1.6;">
                    {meta.get('abstract', '')[:400]}...
                </div>
            </div>
        """, unsafe_allow_html=True)
    except Exception:
        pass
 

 
