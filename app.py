import xml.etree.ElementTree as ET
import re
import urllib.request
import pandas as pd
import streamlit as st
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer

# Ładowanie polskiego modelu językowego
@st.cache_resource
def load_nlp():
    return spacy.load("pl_core_news_sm")

nlp = load_nlp()

st.set_page_config(
    page_title="SEO Tools AI",
    page_icon="🤖",
    layout="wide"
)

# Nagłówek aplikacji
st.markdown("""
    <h1>SEO Tools AI</h1>
    <p>Proste narzędzia SEO wykorzystujące AI do codziennej pracy.</p>
    <hr style="margin-bottom: 2em;">
""", unsafe_allow_html=True)

st.subheader("🔗 Generator Linkowania Wewnętrznego")
st.caption("Analizuje tematykę wpisu i automatycznie dobiera najbardziej pasujące adresy z sitemapy.")

if "topics" not in st.session_state:
    st.session_state.topics = None

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("1. Wprowadź dane")
    sitemap_input = st.text_input("Adres Sitemapy XML:", placeholder="https://twojadomena.pl/sitemap.xml")
    text_input = st.text_area("Tekst do analizy:", height=300, placeholder="Wklej tutaj treść artykułu...")

    analyze_topic_btn = st.button("📊 Krok 1: Sprawdź tematykę wpisu", type="secondary")


def extract_key_topics(text, top_n=5):
    doc = nlp(text.lower())
    words = [token.lemma_ for token in doc if token.pos_ in ["NOUN", "ADJ"] and len(token.lemma_) > 3 and not token.is_stop]

    if not words:
        return []

    cleaned_text = " ".join(words)
    vectorizer = TfidfVectorizer(max_features=top_n)
    tfidf_matrix = vectorizer.fit_transform([cleaned_text])
    feature_names = vectorizer.get_feature_names_out()

    return list(feature_names)


def fetch_and_parse_xml(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as response:
        xml_data = response.read()
    return ET.fromstring(xml_data)


def get_urls_from_sitemap(url, visited=None):
    if visited is None:
        visited = set()

    if url in visited:
        return []
    visited.add(url)

    urls = []
    try:
        root = fetch_and_parse_xml(url)
    except Exception:
        return urls

    sub_sitemaps = []
    page_urls = []

    for elem in root.iter():
        if elem.tag.endswith('loc') and elem.text:
            loc = elem.text.strip()
            if loc.endswith('.xml') or 'sitemap' in loc.lower():
                sub_sitemaps.append(loc)
            else:
                page_urls.append(loc)

    urls.extend(page_urls)

    for sub_url in sub_sitemaps:
        if sub_url not in visited:
            urls.extend(get_urls_from_sitemap(sub_url, visited))

    return list(dict.fromkeys(urls))


if analyze_topic_btn:
    if text_input.strip():
        with st.spinner("Analizowanie tekstu pod kątem tematyki..."):
            st.session_state.topics = extract_key_topics(text_input)
    else:
        st.error("Wklej tekst do pola po lewej stronie.")

with col2:
    st.subheader("2. Raport Tematyczny & Linkowanie")

    if st.session_state.topics:
        st.success("✅ Wykryto główną tematykę wpisu!")
        
        st.write("**Główne tematy / Słowa kluczowe artykułu:**")
        st.write(" ".join([f"`{topic.upper()}`" for topic in st.session_state.topics]))

        st.divider()
        
        match_links_btn = st.button("🔗 Krok 2: Dopasuj linki z sitemapy do wykrytej tematyki", type="primary")

        if match_links_btn:
            if not sitemap_input:
                st.error("Podaj adres sitemapy XML!")
            else:
                with st.spinner("Przeszukiwanie sitemapy i filtrowanie według tematu..."):
                    try:
                        urls = get_urls_from_sitemap(sitemap_input)
                        matched_results = []

                        for url in urls:
                            slug = url.rstrip("/").split("/")[-1].replace("-", " ")
                            slug_doc = nlp(slug.lower())
                            slug_lemmas = [t.lemma_ for t in slug_doc]

                            for topic in st.session_state.topics:
                                if topic in slug_lemmas or topic in slug:
                                    matched_results.append({
                                        "Kategoria / Temat": topic.upper(),
                                        "Słowo z URL": slug,
                                        "Sugerowany URL": url
                                    })

                        if matched_results:
                            df = pd.DataFrame(matched_results).drop_duplicates(subset=["Sugerowany URL"])
                            st.dataframe(df, use_container_width=True)

                            csv_data = df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Pobierz raport CSV",
                                data=csv_data,
                                file_name="linki_tematyczne.csv",
                                mime="text/csv"
                            )
                        else:
                            st.info("Nie znaleziono w sitemapie adresów pasujących do tej konkretnej tematyki.")
                    except Exception as e:
                        st.error(f"Błąd: {e}")
    else:
        st.info("Wklej artykuł po lewej stronie i kliknij 'Sprawdź tematykę wpisu', aby rozpocząć.")
