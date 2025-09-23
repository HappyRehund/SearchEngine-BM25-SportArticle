import streamlit as st
import json
import os
from pyserini.search.lucene import LuceneSearcher

# --- Konfigurasi Awal (dijalankan sekali) ---
@st.cache_resource
def load_searcher_and_data():
    """Memuat searcher Pyserini dan data asli untuk menghindari loading berulang."""
    
    # --- VALIDASI AWAL ---
    INDEX_PATH = 'indexes/detik_sport'
    JSON_PATH = 'detik_sport_articles_combined.json'

    if not os.path.exists(INDEX_PATH):
        st.error(f"Direktori indeks tidak ditemukan di: '{INDEX_PATH}'.")
        st.info("Pastikan Anda sudah menjalankan skrip indexing untuk membuat indeks Pyserini.")
        return None, None

    if not os.path.exists(JSON_PATH):
        st.error(f"File data tidak ditemukan di: '{JSON_PATH}'.")
        st.info("Pastikan Anda sudah menjalankan skrip scraping untuk membuat file JSON.")
        return None, None
    # --- AKHIR VALIDASI ---

    try:
        # Tampilkan pesan loading agar pengguna tahu apa yang terjadi
        with st.spinner("Memuat indeks pencarian... Ini mungkin butuh beberapa saat."):
            searcher = LuceneSearcher(INDEX_PATH)
            searcher.set_language('id')
    except Exception as e:
        st.error(f"Gagal memuat indeks Pyserini dari '{INDEX_PATH}'.")
        st.error(f"Error: {e}")
        return None, None

    # Muat data asli untuk mendapatkan metadata (title, url, dll.)
    with st.spinner("Memuat data artikel..."):
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            articles_list = json.load(f)
            articles_dict = {article['url']: article for article in articles_list}
        
    return searcher, articles_dict

# --- Tampilan Aplikasi ---
st.title("⚽ Detik Sport Search Engine")
st.write("Ditenagai oleh Pyserini dengan model BM25.")

# Muat searcher dan data
searcher, articles_data = load_searcher_and_data()

if searcher and articles_data:
    # Buat search bar
    query = st.text_input("Masukkan query pencarian:", placeholder="Contoh: Jadwal liga malam ini")

    if query:
        st.write(f"Hasil pencarian untuk: **{query}**")

        # Lakukan pencarian menggunakan Pyserini
        hits = searcher.search(query, k=10) # Ambil top 10 hasil

        if not hits:
            st.warning("Tidak ada hasil yang ditemukan.")
        else:
            # Tampilkan hasil
            for i, hit in enumerate(hits):
                doc_id = hit.docid  # Ini adalah URL artikel
                score = hit.score
                
                # Ambil data lengkap dari dictionary yang sudah kita muat
                article_info = articles_data.get(doc_id)
                
                if article_info:
                    st.subheader(f"{i+1}. {article_info['title']}")
                    st.markdown(f"**Tanggal:** {article_info['date']} | **Penulis:** {article_info['author']}")
                    st.markdown(f"Skor Relevansi (BM25): **{score:.4f}**")
                    
                    # Buat link yang bisa diklik
                    st.markdown(f"Baca selengkapnya: [{article_info['url']}]({article_info['url']})")
                    st.write("---")
                else:
                    st.warning(f"Tidak dapat menemukan detail untuk artikel dengan ID: {doc_id}")
else:
    st.info("Aplikasi sedang menunggu indeks Pyserini dimuat atau dibuat.")