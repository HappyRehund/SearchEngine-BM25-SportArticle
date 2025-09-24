import json
import re
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory


def preprocess_data_for_pyserini(input_file, output_file):
    """
    Membaca data JSON asli, membersihkan, dan mengubah formatnya 
    menjadi JSONL yang siap diindeks oleh Pyserini.
    """
    factory = StemmerFactory()
    stemmer = factory.create_stemmer()
    stop_factory = StopWordRemoverFactory()
    stop_remover = stop_factory.create_stop_word_remover()
    
    print(f"Membaca data dari {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        articles = json.load(f)

    unwanted_phrases = [
        "SCROLL TO CONTINUE WITH CONTENT",
        "ADVERTISEMENT",
        # Klo mau ngehapus frasa ngga penting disini
    ]

    domain_stopwords = [
        'baca','juga', 'jakarta', 'wib', 'vs', 'fc', 'di', 'pada', 'dalam', 'dan', 'itu',
        'ini', 'skor', 'foto', 'video', 'krs', 'yna', 'aff', 'pur', 'mrp', 'cas', 'adp', 'rin', 'nds', 'mcy'
    ]
    print(f"Memproses {len(articles)} artikel dan menyimpannya ke {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f_out:
        for i, article in enumerate(articles):
            # Membersihkan title dan content
            title = article.get('title', '').strip()
            content = article.get('content', '').strip()

            # Hapus frasa-frasa yang tidak diinginkan dari content
            for phrase in unwanted_phrases:
                content = content.replace(phrase, '')

            # Hapus teks video di akhir seperti "[Gambas:Video 20detik]" atau "(yna/aff)"
            content = re.sub(r'\[Gambas:Video.*?\]', '', content)
            content = re.sub(r'\(\w+\/\w+\)$', '', content)

            combined_content = f"{title}. {content.strip()}"

            #1. Case folding
            processed_content = combined_content.lower()

            #2. menghapus tanda baca dan angka
            processed_content = re.sub(r'[^a-z\s]', ' ', processed_content)

            #3. menghapus domain spesific stopword
            words = processed_content.split()
            words = [word for word in words if word not in domain_stopwords]
            processed_content = ' '.join(words)

            print(f"Stemming artikel {i+1}/{len(articles)}: {title[:30]}")
            no_stop = stop_remover.remove(processed_content)
            stemmed_content = stemmer.stem(no_stop)
            
            # Buat format JSONL yang dibutuhkan Pyserini
            # "id" harus unik, kita bisa gunakan URL
            pyserini_doc = {
                "id": article.get('url'),
                "contents": stemmed_content
            }

            # Tulis sebagai satu baris JSON ke file output
            f_out.write(json.dumps(pyserini_doc, ensure_ascii=False) + '\n')
            
    print("Preprocessing selesai!")

if __name__ == '__main__':
    INPUT_JSON = 'detik_sport_articles_combined.json'
    OUTPUT_JSONL_STEMMED = 'pyserini_corpus_stemmed.jsonl'
    preprocess_data_for_pyserini(INPUT_JSON, OUTPUT_JSONL_STEMMED)