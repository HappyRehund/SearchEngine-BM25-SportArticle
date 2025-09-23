import os
import json
import streamlit as st
from pyserini.search.lucene import LuceneSearcher
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

INDEX_PATH = "indexes/detik_sport"
JSON_PATH = "detik_sport_articles_combined.json"

st.set_page_config(page_title="Detik Sport Search", page_icon="🏃", layout="wide")
st.title("🏃 Detik Sport Search")
st.caption("Pencarian artikel menggunakan Pyserini (BM25) + stemming Sastrawi")

@st.cache_resource(show_spinner=False)
def load_resources(index_path: str, json_path: str):
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"Direktori index tidak ditemukan: {index_path}")
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"File data tidak ditemukan: {json_path}")

    searcher = LuceneSearcher(index_path)
    searcher.set_language("id")

    with open(json_path, "r", encoding="utf-8") as f:
        articles_list = json.load(f)

    articles_data = {article["url"]: article for article in articles_list}

    factory = StemmerFactory()
    stemmer = factory.create_stemmer()

    return searcher, articles_data, stemmer

try:
    with st.spinner("Memuat indeks dan data artikel..."):
        searcher, articles_data, stemmer = load_resources(INDEX_PATH, JSON_PATH)
    st.success(f"Indeks & data siap. Total artikel: {len(articles_data)}")
except Exception as e:
    st.error(f"Gagal memuat resource: {e}")
    st.stop()

with st.sidebar:
    st.header("Opsi Pencarian")
    use_stemming = st.checkbox("Gunakan stemming (Sastrawi)", value=True)
    top_k = st.slider("Jumlah hasil (k)", min_value=5, max_value=50, value=10, step=5)

query = st.text_input("Masukkan kata kunci", value="", placeholder="Contoh: Onana, persib, liga 1, timnas...")

col1, col2 = st.columns([1, 3])
with col1:
    search_btn = st.button("Cari", type="primary")
with col2:
    st.write("")

st.divider()

def shorten(text: str, max_len: int = 400):
    if not text:
        return ""
    text = text.strip().replace("\n", " ")
    return text if len(text) <= max_len else text[: max_len - 1].rstrip() + "…"

if search_btn:
    if not query.strip():
        st.warning("Silakan masukkan query terlebih dahulu.")
    else:
        processed_query = stemmer.stem(query) if use_stemming else query
        with st.spinner("Mencari..."):
            hits = searcher.search(processed_query, k=top_k)

        st.write(f"Query: “{query}”")
        if use_stemming:
            st.caption(f"Setelah stemming: “{processed_query}”")
        st.subheader(f"Hasil: {len(hits)} dokumen")

        if not hits:
            st.info("Tidak ada hasil yang ditemukan.")
        else:
            for i, hit in enumerate(hits, start=1):
                doc_id = hit.docid
                score = hit.score

                article = articles_data.get(doc_id)

                with st.container(border=True):
                    st.markdown(f"**#{i} — Skor BM25: {score:.4f}**")
                    if article:
                        st.markdown(f"### {article.get('title', '(Tanpa Judul)')}")
                        meta = []
                        if article.get("date"):
                            meta.append(article['date'])
                        if article.get("url"):
                            meta.append(f"[Buka Artikel]({article['url']})")
                        if meta:
                            st.caption(" • ".join(meta))
                        snippet = shorten(article.get("content", ""))
                        if snippet:
                            st.write(snippet)
                    else:
                        st.warning(f"Detail artikel tidak ditemukan untuk doc_id: {doc_id}")