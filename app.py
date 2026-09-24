import xml.etree.ElementTree as ET
import re
import urllib.request
import pandas as pd
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.corpus import stopwords

# Konfiguracja strony
st.set_page_config(
    page_title="SEO Tools AI",
    page_icon="🤖",
    layout="wide"
)

# Pobieranie polskich stopwords
@st.cache_resource
def setup_nltk():
    nltk.download('stopwords', quiet=True)
    try:
        polish_stopwords = set(stopwords.words('polish'))
    except Exception:
        polish_stopwords = {
            'oraz', 'jest', 'jako', 'przez', 'tylko', 'może', 'jego', 
            'być', 'jeśli', 'więc', 'który', 'która', 'które', 'jak', 'tak', 
            'dla', 'tego', 'brak', 'czy', 'żeby', 'tutaj', 'gdzie'
        }
    return polish_stopwords

PL_STOPWORDS = setup_nltk()

# Zarządzanie stanem nawigacji (Narzędzie vs Strona Główna)
if "current_tool" not in st.session_state:
    st.session_state.current_tool = "home"

if "topics" not in st.session_state:
    st.session_state.topics = None

# --- FUNKCJE POMOCNICZE ---
def extract_key_topics(text, top_n=6):
    clean_text = re.sub(r'[^\w\s]', '', text.lower())
    words = [word for word in clean_text.split() if len(word) > 3 and word not in PL_STOPWORDS]

    if not words:
        return []

    cleaned_string = " ".join(words)
    vectorizer = TfidfVectorizer(max_features=top_n)
    vectorizer.fit_transform([cleaned_string])
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

def suggest_internal_links(text, urls):
    suggestions = []
    for url in urls:
        slug = url.rstrip("/").split("/")[-1]
        keyword = slug.replace("-", " ")

        if len(keyword) < 4:
            continue

        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        match = re.search(pattern, text)

        if match:
            suggestions.append({
                "Dopasowana fraza": match.group(0),
                "Sugerowany Anchor": keyword,
                "Docelowy URL": url
            })
    return suggestions


# ==========================================
# EKRAN 1: STRONA GŁÓWNA (KARTY NARZĘDZI)
# ==========================================
if st.session_state.current_tool == "home":
    st.markdown("""
        <h1>SEO Tools AI</h1>
        <p>Proste narzędzia SEO wykorzystujące AI do codziennej pracy.</p>
        <hr style="margin-bottom: 2em;">
    """, unsafe_allow_html=True)

    st.subheader("Wybierz narzędzie:")
    
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="border:1px solid #e6e6e6; border-radius:10px; padding:20px; text-align:center; box-shadow: 2px 2px 8px rgba(0,0,0,0.05);">
            <h3>🔗 Linkowanie Wewnętrzne</h3>
            <p>Automatycznie dopasowuj adresy URL z sitemapy XML do fraz w Twoim artykule oraz sprawdzaj tematykę wpisu.</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Otwórz narzędzie", key="open_linker", type="primary", use_container_width=True):
            st.session_state.current_tool = "linker"
            st.rerun()

    with col2:
        st.markdown("""
        <div style="border:1px solid #e6e6e6; border-radius:10px; padding:20px; text-align:center; box-shadow: 2px 2px 8px rgba(0,0,0,0.05); color: #888;">
            <h3>📝 Generator Meta Description</h3>
            <p>Twórz zoptymalizowane pod SEO opisy meta na podstawie wklejonego artykułu.</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        st.button("Wkrótce...", key="meta_gen", disabled=True, use_container_width=True)

    with col3:
        st.markdown("""
        <div style="border:1px solid #e6e6e6; border-radius:10px; padding:20px; text-align:center; box-shadow: 2px 2px 8px rgba(0,0,0,0.05); color: #888;">
            <h3>🔍 Analizator Słów Kluczowych</h3>
            <p>Szybkie wyciąganie głównych intencji i fraz kluczowych z treści konkurencji.</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        st.button("Wkrótce...", key="kw_analyzer", disabled=True, use_container_width=True)


# ==========================================
# EKRAN 2: NARZĘDZIE LINKOWANIA WEWNĘTRZNEGO
# ==========================================
elif st.session_state.current_tool == "linker":
    if st.button("← Powrót do menu narzędzi"):
        st.session_state.current_tool = "home"
        st.rerun()

    st.markdown("<h1>🔗 Generator Linkowania Wewnętrznego</h1>", unsafe_allow_html=True)
    st.caption("Dopasowuj linki bezpośrednio do słów kluczowych lub sprawdzaj główną tematykę wpisu.")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("1. Wprowadź dane")
        sitemap_input = st.text_input("Adres Sitemapy XML:", placeholder="https://twojadomena.pl/sitemap.xml")
        text_input = st.text_area("Tekst do analizy:", height=300, placeholder="Wklej tutaj treść artykułu...")

        st.write("---")
        
        # Przycisk podstawowy (jak w oryginalnej wersji)
        analyze_links_btn = st.button("🚀 Dopasuj linki z sitemapy", type="primary", use_container_width=True)
        
        # Nowy przycisk do sprawdzania tematyki
        analyze_topic_btn = st.button("📊 Analizuj tematykę wpisu", type="secondary", use_container_width=True)


    with col2:
        st.subheader("2. Wyniki analizy")

        # LOGIKA 1: Standardowe dopasowywanie linków (poprzednia funkcjonalność)
        if analyze_links_btn:
            if not sitemap_input or not text_input:
                st.error("⚠️ Proszę podać adres sitemapy oraz wkleić tekst.")
            else:
                with st.spinner("Skanowanie sitemapy i szukanie powiązań w tekście..."):
                    try:
                        urls = get_urls_from_sitemap(sitemap_input)
                        results = suggest_internal_links(text_input, urls)

                        st.success(f"Pobrano {len(urls)} adresów URL z sitemapy.")
                        
                        if results:
                            df = pd.DataFrame(results)
                            st.dataframe(df, use_container_width=True)
                            
                            csv_data = df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Pobierz raport CSV",
                                data=csv_data,
                                file_name="linkowanie_wewnetrzne.csv",
                                mime="text/csv"
                            )
                        else:
                            st.info("Nie znaleziono w tekście dokładnych dopasowań słów kluczowych ze slugów sitemapy.")
                    except Exception as e:
                        st.error(f"❌ Błąd podczas pobierania sitemapy: {e}")

        # LOGIKA 2: Nowa opcja - Sprawdzanie tematyki wpisu
        elif analyze_topic_btn:
            if not text_input.strip():
                st.error("⚠️ Wklej tekst artykułu po lewej stronie.")
            else:
                with st.spinner("Analizowanie tematyki artykułu..."):
                    topics = extract_key_topics(text_input)
                    st.session_state.topics = topics
                    
                    if topics:
                        st.success("✅ Wykryto główne tematy artykułu!")
                        st.write("**Główne słowa kluczowe i tematyka:**")
                        
                        # Wyświetlanie znalezionych tematów w ładnych boksach
                        st.write(" ".join([f"`{topic.upper()}`" for topic in topics]))
                        
                        st.divider()

                        # Jeśli podano sitemapę, od razu proponuje adresy pasujące tematycznie
                        if sitemap_input:
                            st.write("**Sugerowane podstrony z sitemapy dopasowane do tematyki:**")
                            urls = get_urls_from_sitemap(sitemap_input)
                            matched_topics = []

                            for url in urls:
                                slug = url.rstrip("/").split("/")[-1].replace("-", " ").lower()
                                for topic in topics:
                                    topic_stem = topic[:5] if len(topic) > 5 else topic
                                    if topic_stem in slug or topic in slug:
                                        matched_topics.append({
                                            "Wykryty temat": topic.upper(),
                                            "Pasujący URL z sitemapy": url
                                        })

                            if matched_topics:
                                df_topics = pd.DataFrame(matched_topics).drop_duplicates(subset=["Pasujący URL z sitemapy"])
                                st.dataframe(df_topics, use_container_width=True)
                            else:
                                st.info("Brak podstron w sitemapie pasujących do wykrytej tematyki.")
                    else:
                        st.warning("Nie udało się wyodrębnić jednoznacznych słów kluczowych.")
        else:
            st.info("Podaj adres sitemapy, wklej artykuł po lewej stronie i wybierz odpowiednią akcję.")
