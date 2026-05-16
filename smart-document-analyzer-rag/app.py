from __future__ import annotations

from html import escape

import streamlit as st

from src.document_loader import load_uploaded_file
from src.rag_pipeline import RagPipeline


st.set_page_config(
    page_title="Smart Document Analyzer",
    page_icon="",
    layout="wide",
)


def main() -> None:
    _inject_css()
    _init_state()

    st.markdown(
        """
        <section class="hero-band">
            <div>
                <p class="eyebrow">AI document intelligence</p>
                <h1>Smart Document Analyzer</h1>
                <p class="hero-copy">
                    Grounded answers from PDFs, reports, policies, notes, and research files.
                </p>
            </div>
            <div class="hero-status">
                <span>RAG pipeline</span>
                <strong>Retrieval ready</strong>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown('<div class="sidebar-title">Retrieval Settings</div>', unsafe_allow_html=True)
        chunk_size = st.slider("Chunk size", min_value=250, max_value=1500, value=900, step=50)
        overlap = st.slider("Chunk overlap", min_value=0, max_value=400, value=150, step=25)
        top_k = st.slider("Retrieved chunks", min_value=1, max_value=8, value=4, step=1)

        st.divider()
        st.markdown(
            """
            <div class="sidebar-note">
                Upload files, process them into searchable chunks, then ask questions from the document.
            </div>
            """,
            unsafe_allow_html=True,
        )

    summary = st.session_state.pipeline.summary
    _render_metrics(summary)
    _render_project_info()

    upload_col, query_col = st.columns([1.05, 0.95], gap="large")

    with upload_col:
        st.markdown('<div class="panel-heading">Document Intake</div>', unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Upload source files",
            type=["pdf", "docx", "txt", "md"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )

        if uploaded_files:
            st.markdown('<div class="file-list-title">Selected files</div>', unsafe_allow_html=True)
            for uploaded_file in uploaded_files:
                st.markdown(f'<div class="file-pill">{escape(uploaded_file.name)}</div>', unsafe_allow_html=True)

        build_clicked = st.button("Process uploaded documents", type="primary", disabled=not uploaded_files)
        if build_clicked:
            _build_index(uploaded_files, chunk_size, overlap)

    with query_col:
        st.markdown('<div class="panel-heading">Ask The Index</div>', unsafe_allow_html=True)
        question = st.text_input(
            "Question",
            placeholder="Example: What are the main risks mentioned in this document?",
            label_visibility="collapsed",
        )
        ask_clicked = st.button("Analyze document", disabled=not question or summary.chunk_count == 0)

        if not summary.chunk_count:
            st.info("Upload a document and click Process uploaded documents before asking a question.")

    if ask_clicked:
        _answer_question(question, top_k)


def _init_state() -> None:
    if "pipeline" not in st.session_state:
        st.session_state.pipeline = RagPipeline()
    if "indexed_files" not in st.session_state:
        st.session_state.indexed_files = []


def _inject_css() -> None:
    st.markdown(
        """
        <style>
            :root {
                --ink: #20242a;
                --muted: #68736f;
                --paper: #fbfcf8;
                --surface: #ffffff;
                --line: #dce3dc;
                --teal: #007c75;
                --teal-dark: #123d3a;
                --amber: #d99a27;
                --coral: #c85b4a;
            }

            .stApp {
                background:
                    linear-gradient(180deg, rgba(246, 249, 244, 0.96), rgba(240, 244, 239, 0.98)),
                    repeating-linear-gradient(90deg, rgba(0, 124, 117, 0.06) 0 1px, transparent 1px 72px);
                color: var(--ink);
            }

            [data-testid="stHeader"] {
                background: rgba(246, 249, 244, 0.86);
                border-bottom: 1px solid rgba(220, 227, 220, 0.65);
                backdrop-filter: blur(14px);
            }

            .block-container {
                max-width: 1180px;
                padding-top: 2.1rem;
                padding-bottom: 4rem;
            }

            section[data-testid="stSidebar"] {
                background: linear-gradient(180deg, #102522 0%, #16332f 100%);
                border-right: 1px solid rgba(255, 255, 255, 0.08);
            }

            section[data-testid="stSidebar"] * {
                color: #eef7f2;
            }

            section[data-testid="stSidebar"] .stSlider label,
            section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
                color: rgba(238, 247, 242, 0.82);
            }

            .sidebar-title {
                color: #ffffff;
                font-size: 0.92rem;
                font-weight: 800;
                letter-spacing: 0.08em;
                margin-bottom: 1rem;
                text-transform: uppercase;
            }

            .sidebar-note {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-left: 3px solid var(--amber);
                border-radius: 8px;
                color: rgba(238, 247, 242, 0.86);
                font-size: 0.86rem;
                line-height: 1.5;
                padding: 0.85rem;
            }

            .hero-band {
                align-items: stretch;
                background:
                    linear-gradient(135deg, #123d3a 0%, #0d6963 58%, #d99a27 120%);
                border: 1px solid rgba(255, 255, 255, 0.24);
                border-radius: 8px;
                box-shadow: 0 20px 60px rgba(18, 61, 58, 0.18);
                color: #ffffff;
                display: flex;
                justify-content: space-between;
                margin-bottom: 1.25rem;
                min-height: 184px;
                overflow: hidden;
                padding: 2rem;
                position: relative;
            }

            .hero-band::after {
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.18), transparent);
                content: "";
                height: 100%;
                position: absolute;
                right: 24%;
                top: 0;
                transform: skewX(-18deg);
                width: 92px;
            }

            .hero-band h1 {
                color: #ffffff;
                font-size: clamp(2.3rem, 5vw, 4.6rem);
                font-weight: 850;
                letter-spacing: 0;
                line-height: 0.98;
                margin: 0;
                max-width: 760px;
            }

            .eyebrow {
                color: rgba(255, 255, 255, 0.78);
                font-size: 0.78rem;
                font-weight: 800;
                letter-spacing: 0.14em;
                margin: 0 0 0.75rem;
                text-transform: uppercase;
            }

            .hero-copy {
                color: rgba(255, 255, 255, 0.88);
                font-size: 1.05rem;
                line-height: 1.55;
                margin: 1rem 0 0;
                max-width: 620px;
            }

            .hero-status {
                align-self: flex-end;
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.22);
                border-radius: 8px;
                min-width: 190px;
                padding: 1rem;
                position: relative;
                z-index: 1;
            }

            .hero-status span {
                color: rgba(255, 255, 255, 0.72);
                display: block;
                font-size: 0.76rem;
                font-weight: 800;
                letter-spacing: 0.08em;
                margin-bottom: 0.3rem;
                text-transform: uppercase;
            }

            .hero-status strong {
                color: #ffffff;
                display: block;
                font-size: 1.05rem;
            }

            [data-testid="stMetric"] {
                background: rgba(255, 255, 255, 0.92);
                border: 1px solid var(--line);
                border-radius: 8px;
                box-shadow: 0 12px 28px rgba(42, 54, 49, 0.06);
                padding: 1rem 1rem 0.85rem;
            }

            [data-testid="stMetricLabel"] {
                color: var(--muted);
                font-size: 0.78rem;
                font-weight: 800;
                letter-spacing: 0.08em;
                text-transform: uppercase;
            }

            [data-testid="stMetricValue"] {
                color: var(--ink);
                font-weight: 850;
            }

            .panel-heading {
                color: var(--ink);
                font-size: 1rem;
                font-weight: 850;
                letter-spacing: 0;
                margin: 1.7rem 0 0.6rem;
            }

            div[data-testid="stFileUploader"] {
                background: rgba(255, 255, 255, 0.94);
                border: 1px dashed rgba(0, 124, 117, 0.45);
                border-radius: 8px;
                box-shadow: 0 14px 32px rgba(42, 54, 49, 0.06);
                padding: 1rem;
            }

            div[data-testid="stFileUploader"] section {
                background: rgba(0, 124, 117, 0.04);
                border: 0;
                border-radius: 8px;
            }

            div[data-testid="stFileUploader"] button {
                background: var(--teal) !important;
                border: 1px solid var(--teal) !important;
                border-radius: 8px !important;
                box-shadow: 0 8px 18px rgba(0, 124, 117, 0.18);
                color: #ffffff !important;
                font-weight: 800;
            }

            div[data-testid="stFileUploader"] button:hover {
                background: var(--teal-dark) !important;
                border-color: var(--teal-dark) !important;
                color: #ffffff !important;
            }

            div[data-testid="stFileUploader"] button *,
            div[data-testid="stFileUploader"] button svg {
                color: #ffffff !important;
                fill: #ffffff !important;
                stroke: #ffffff !important;
            }

            .file-list-title {
                color: var(--muted);
                font-size: 0.78rem;
                font-weight: 800;
                letter-spacing: 0.08em;
                margin: 0.9rem 0 0.45rem;
                text-transform: uppercase;
            }

            .file-pill {
                background: #ffffff;
                border: 1px solid var(--line);
                border-left: 3px solid var(--teal);
                border-radius: 8px;
                color: var(--ink);
                font-size: 0.9rem;
                font-weight: 650;
                margin-bottom: 0.45rem;
                overflow-wrap: anywhere;
                padding: 0.72rem 0.85rem;
            }

            .stTextInput input {
                background: #ffffff;
                border: 1px solid var(--line);
                border-radius: 8px;
                color: var(--ink);
                min-height: 3.15rem;
            }

            .stTextInput input::placeholder {
                color: #7b8580;
                opacity: 1;
            }

            .stTextInput input:focus {
                border-color: var(--teal);
                box-shadow: 0 0 0 3px rgba(0, 124, 117, 0.12);
            }

            .stButton > button {
                border-radius: 8px;
                font-weight: 800;
                min-height: 3rem;
                transition: transform 150ms ease, box-shadow 150ms ease, border-color 150ms ease;
                width: 100%;
            }

            .stButton > button:hover {
                border-color: var(--teal);
                box-shadow: 0 10px 20px rgba(0, 124, 117, 0.12);
                transform: translateY(-1px);
            }

            .stButton > button[kind="secondary"] {
                background: var(--coral);
                border-color: var(--coral);
                color: #ffffff;
            }

            .stButton > button[kind="secondary"]:hover {
                background: #a94537;
                border-color: #a94537;
                box-shadow: 0 10px 22px rgba(200, 91, 74, 0.2);
                color: #ffffff;
            }

            .stButton > button:disabled,
            .stButton > button:disabled:hover {
                background: #f1ded9;
                border-color: #dfb8af;
                box-shadow: none;
                color: #7a4b42;
                transform: none;
            }

            .stButton > button[kind="primary"] {
                background: var(--teal);
                border-color: var(--teal);
                color: #ffffff;
            }

            .stButton > button:disabled,
            .stButton > button:disabled:hover {
                background: #f1ded9 !important;
                border-color: #dfb8af !important;
                box-shadow: none !important;
                color: #7a4b42 !important;
                cursor: not-allowed;
                transform: none !important;
            }

            .stAlert {
                border-radius: 8px;
            }

            .answer-card {
                background: #ffffff;
                border: 1px solid var(--line);
                border-left: 4px solid var(--teal);
                border-radius: 8px;
                box-shadow: 0 16px 38px rgba(42, 54, 49, 0.07);
                color: var(--ink);
                font-size: 1rem;
                line-height: 1.65;
                margin-top: 0.8rem;
                padding: 1.15rem 1.25rem;
                white-space: pre-wrap;
            }

            .answer-mode {
                color: var(--muted);
                font-size: 0.82rem;
                font-weight: 750;
                margin-top: 0.45rem;
            }

            .info-grid {
                display: grid;
                gap: 0.85rem;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                margin-top: 1rem;
            }

            .info-card {
                background: rgba(255, 255, 255, 0.92);
                border: 1px solid var(--line);
                border-radius: 8px;
                box-shadow: 0 12px 28px rgba(42, 54, 49, 0.055);
                min-height: 126px;
                padding: 1rem;
            }

            .info-card span {
                color: var(--muted);
                display: block;
                font-size: 0.72rem;
                font-weight: 850;
                letter-spacing: 0.08em;
                margin-bottom: 0.45rem;
                text-transform: uppercase;
            }

            .info-card strong {
                color: var(--ink);
                display: block;
                font-size: 1.35rem;
                line-height: 1.1;
                margin-bottom: 0.5rem;
            }

            .info-card p {
                color: var(--muted);
                font-size: 0.86rem;
                line-height: 1.45;
                margin: 0;
            }

            div[data-testid="stExpander"] details {
                background: rgba(255, 255, 255, 0.92);
                border: 1px solid var(--line);
                border-radius: 8px;
                box-shadow: 0 10px 24px rgba(42, 54, 49, 0.05);
            }

            div[data-testid="stExpander"] summary {
                color: var(--ink);
                font-weight: 800;
            }

            @media (max-width: 760px) {
                .block-container {
                    padding-top: 1.2rem;
                }

                .hero-band {
                    display: block;
                    padding: 1.35rem;
                }

                .hero-band h1 {
                    font-size: 2.4rem;
                }

                .hero-status {
                    margin-top: 1.2rem;
                    min-width: 0;
                }

                .info-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_metrics(summary) -> None:
    indexed_files = st.session_state.get("indexed_files", [])
    mode = "Local RAG" if summary.chunk_count else "Waiting"

    doc_col, chunk_col, mode_col = st.columns(3)
    doc_col.metric("Documents", summary.document_count)
    chunk_col.metric("Chunks", summary.chunk_count)
    mode_col.metric("Answer Mode", mode)

    if indexed_files:
        st.caption(f"Indexed files: {', '.join(indexed_files)}")


def _render_project_info() -> None:
    st.markdown(
        """
        <div class="panel-heading">Project Intelligence Summary</div>
        <section class="info-grid">
            <div class="info-card">
                <span>Trained models</span>
                <strong>0</strong>
                <p>This project does not train a new ML model. It uses RAG over uploaded documents.</p>
            </div>
            <div class="info-card">
                <span>Retrieval model</span>
                <strong>TF-IDF</strong>
                <p>A local vector-style index is fitted at runtime for the current uploaded files.</p>
            </div>
            <div class="info-card">
                <span>Answer engine</span>
                <strong>Local</strong>
                <p>Extractive answers work without an API key; a cloud LLM can be connected later.</p>
            </div>
            <div class="info-card">
                <span>Cloud path</span>
                <strong>Ready</strong>
                <p>The local index can be upgraded to Pinecone, Chroma, or Azure AI Search.</p>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _build_index(uploaded_files, chunk_size: int, overlap: int) -> None:
    with st.spinner("Reading documents and building the retrieval index..."):
        try:
            documents = [load_uploaded_file(uploaded_file) for uploaded_file in uploaded_files]
            st.session_state.pipeline = RagPipeline()
            st.session_state.pipeline.build_index(documents, chunk_size=chunk_size, overlap=overlap)
            st.session_state.indexed_files = [document.filename for document in documents]
        except Exception as exc:
            st.error(f"Could not build the document index: {exc}")


def _answer_question(question: str, top_k: int) -> None:
    with st.spinner("Retrieving context and generating an answer..."):
        try:
            response = st.session_state.pipeline.ask(question, top_k=top_k)
        except Exception as exc:
            st.error(f"Could not analyze the question: {exc}")
            return

    st.markdown('<div class="panel-heading">Answer</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="answer-card">{escape(response.answer.text)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="answer-mode">Answer mode: {escape(response.answer.mode)}</div>', unsafe_allow_html=True)

    st.markdown('<div class="panel-heading">Retrieved Sources</div>', unsafe_allow_html=True)
    if not response.sources:
        st.info("No matching source chunks were found.")
        return

    for result in response.sources:
        with st.expander(f"{result.chunk.chunk_id} | relevance {result.score:.3f}"):
            st.write(result.chunk.text)


if __name__ == "__main__":
    main()
