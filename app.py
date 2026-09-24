import os
import xml.etree.ElementTree as ET
import urllib.request
import pandas as pd
import streamlit as st
import trafilatura

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Konfiguracja strony
st.set_page_config(
    page_title="SEO Tools AI",
    page_icon="🤖",
    layout="wide"
)

if "current_tool" not in st.session_state:
    st.session_state.current_tool = "home"

# --- FUNKCJE POMOCNICZE ---

def extract_text_from_url(url):
    """Pobiera czysty tekst artykułu ze wskazanego adresu URL."""
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded)
            if text:
                return text
        return None
    except Exception as e:
        st.error(f"Błąd podczas pobierania treści z URL: {e}")
        return None

def fetch_and_parse_xml(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
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

def analyze_with_ai(api_key, article_text, urls):
    """Analizuje treść i sitemapę za pomocą OpenAI GPT-4o-mini."""
    client = OpenAI(api_key=api_key)

    # Przekazujemy maksymalnie 150 adresów URL z sitemapy
    urls_formatted = "\n".join(urls[:150])
    
    prompt = f"""
Przeanalizuj poniższy tekst artykułu oraz listę adresów URL z sitemapy.
Twoim zadaniem jest znalezienie najlepszych powiązań tematycznych pod kątem LINKOWANIA WEWNĘTRZNEGO SEO.

ZWRÓĆ WYNIK W FORMACIE TABELI Z KOLUMNAMI ROZDZIELONYMI ŚREDNIKIEM (;):
Sugerowany Anchor Text;Rekomendowany URL;Uzasadnienie AI

Zasady:
1. Zaproponuj tylko te linki, które idealnie pasują tematycznie do treści artykułu.
2. Zaproponuj konkretny frazowy anchor text (po polsku), który warto podlinkować w tekście.
3. Wyjaśnij krótko w uzasadnieniu, dlaczego ten link pasuje.
4. Zwróć maksymalnie 5-8 najlepszych dopasowań. Nie pisz żadnego wstępu ani podsumowania - tylko linie tabeli.

LISTA URL Z SITEMAPY:
{urls_formatted}

TEKST ARTYKUŁU:
{article_text[:4000]}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Jesteś doświadczonym ekspertem SEO specjalizującym się w linkowaniu wewnętrznym."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    result_text = response.choices[0].message.content.strip()
    
    rows = []
    for line in result_text.split("\n"):
        if ";" in line and not line.startswith("Sugerowany Anchor"):
            parts = line.split(";")
            if len(parts) >= 3:
                rows.append({
                    "Sugerowany Anchor Text": parts[0].strip(),
                    "Rekomendowany URL": parts[1].strip(),
                    "Uzasadnienie AI": parts[2].strip()
                })
    return pd.DataFrame(rows)


# ==========================================
# EKRAN 1: STRONA GŁÓWNA
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
            <h3>🔗 Linkowanie Wewnętrzne AI</h3>
            <p>Automatyczna analiza kontekstowa tekstu i dopasowywanie adresów z sitemapy przy użyciu sztucznej inteligencji.</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Otwórz narzędzie", key="open_linker", type="primary", use_container_width=True):
            st.session_state.current_tool = "linker"
            st.rerun()

    with col2:
        st.button("Wkrótce...", key="meta_gen", disabled=True, use_container_width=True)

    with col3:
        st.button("Wkrótce...", key="kw_analyzer", disabled=True, use_container_width=True)


# ==========================================
# EKRAN 2: NARZĘDZIE LINKOWANIA WEWNĘTRZNEGO
# ==========================================
elif st.session_state.current_tool == "linker":
    if st.button("← Powrót do menu narzędzi"):
        st.session_state.current_tool = "home"
        st.rerun()

    st.markdown("<h1>🔗 Linkowanie Wewnętrzne wspierane przez AI</h1>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("1. Ustawienia i Dane")
        
        # Sposób pobierania klucza API z Secrets
        secret_key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        
        if secret_key:
            st.success("🔒 Klucz OpenAI API został pobrany bezpiecznie z ustawień aplikacji.")
            api_key_input = secret_key
        else:
            api_key_input = st.text_input("Klucz OpenAI API Key:", type="password", help="Wklej klucz lub dodaj go do Secrets w panelu Streamlit Cloud.")

        sitemap_input = st.text_input("Adres Sitemapy XML:", placeholder="https://twojadomena.pl/sitemap.xml")
        input_type = st.radio("Źródło treści artykułu:", ["Wklej tekst ręcznie", "Pobierz treść z adresu URL"], horizontal=True)

        article_text = ""

        if input_type == "Wklej tekst ręcznie":
            article_text = st.text_area("Tekst do analizy:", height=200, placeholder="Wklej tutaj treść artykułu...")
        else:
            article_url = st.text_input("Adres URL artykułu:", placeholder="https://twojadomena.pl/moj-artykul")
            if article_url:
                with st.spinner("Pobieranie treści ze strony..."):
                    fetched_text = extract_text_from_url(article_url)
                    if fetched_text:
                        article_text = fetched_text
                        st.success(f"Pomyślnie pobrano treść ({len(article_text)} znaków).")
                        st.write("**Pobrany tekst:**")
                        with st.container(height=200):
                            st.write(article_text)
                    else:
                        st.error("Nie udało się pobrać treści z podanego URL.")

        st.write("---")
        analyze_ai_btn = st.button("🤖 Analizuj i dopasuj linki z AI", type="primary", use_container_width=True)

    with col2:
        st.subheader("2. Propozycje AI")

        if analyze_ai_btn:
            if not api_key_input:
                st.error("⚠️ Wprowadź Swój Klucz OpenAI API Key lub ustaw go w Secrets.")
            elif not sitemap_input:
                st.error("⚠️ Podaj adres sitemapy XML.")
            elif not article_text.strip():
                st.error("⚠️ Wprowadź tekst lub podaj poprawny URL artykułu.")
            else:
                with st.spinner("AI czyta artykuł, analizuje sitemapę i dobiera linki..."):
                    try:
                        urls = get_urls_from_sitemap(sitemap_input)
                        st.info(f"Pobrano {len(urls)} adresów z sitemapy. Przekazywanie danych do AI...")
                        
                        df_results = analyze_with_ai(api_key_input, article_text, urls)
                        
                        if not df_results.empty:
                            st.success("✅ AI zakończyło analizę!")
                            st.dataframe(df_results, use_container_width=True)
                            
                            csv_data = df_results.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Pobierz raport CSV",
                                data=csv_data,
                                file_name="linkowanie_ai.csv",
                                mime="text/csv"
                            )
                        else:
                            st.warning("AI nie znalazło jednoznacznych powiązań tematycznych.")
                    except Exception as e:
                        st.error(f"❌ Błąd podczas analizy AI: {e}")
        else:
            st.info("Wprowadź dane po lewej stronie i kliknij przycisk, aby AI przeanalizowało kontekst artykułu.")
