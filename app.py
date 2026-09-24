import os
import xml.etree.ElementTree as ET
import urllib.request
import time
import pandas as pd
import streamlit as st
import trafilatura
from urllib.parse import urlparse

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

# Zmienne stanu sesji (Session State)
if "current_tool" not in st.session_state:
    st.session_state.current_tool = "home"
if "detected_keywords" not in st.session_state:
    st.session_state.detected_keywords = None
if "article_text_saved" not in st.session_state:
    st.session_state.article_text_saved = ""
if "sitemap_url_val" not in st.session_state:
    st.session_state.sitemap_url_val = ""
if "article_url_val" not in st.session_state:
    st.session_state.article_url_val = ""


# --- FUNKCJE POMOCNICZE ---

def get_sitemap_from_robots(url_or_domain):
    """Szuka wpisu 'Sitemap:' w pliku robots.txt domeny."""
    try:
        parsed = urlparse(url_or_domain)
        scheme = parsed.scheme if parsed.scheme else "https"
        netloc = parsed.netloc if parsed.netloc else parsed.path.split('/')[0]
        
        if not netloc:
            return None

        robots_url = f"{scheme}://{netloc}/robots.txt"
        
        req = urllib.request.Request(
            robots_url, 
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        
        with urllib.request.urlopen(req, timeout=5) as response:
            content = response.read().decode('utf-8', errors='ignore')
            
        for line in content.splitlines():
            if line.strip().lower().startswith("sitemap:"):
                sitemap_found = line.split(":", 1)[1].strip()
                return sitemap_found
        return None
    except Exception:
        return None


def extract_structured_text_from_url(url):
    """Pobiera treść z URL z zachowaniem nagłówków, list i akapitów (format Markdown)."""
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(
                downloaded, 
                output_format='markdown',
                include_formatting=True,
                include_links=False
            )
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

def get_urls_from_sitemap(url, progress_callback=None, visited=None, total_state=None):
    if visited is None:
        visited = set()
    if total_state is None:
        total_state = {"count": 0}

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
    total_state["count"] += len(page_urls)

    if progress_callback:
        progress_callback(f"Pobrano {total_state['count']} URL-i z sitemapy...")

    for sub_url in sub_sitemaps:
        if sub_url not in visited:
            urls.extend(get_urls_from_sitemap(sub_url, progress_callback, visited, total_state))

    return list(dict.fromkeys(urls))


# --- ANALIZA KROK 1: Wykrywanie słów kluczowych przez AI ---
def extract_keywords_with_ai(api_key, article_text):
    client = OpenAI(api_key=api_key)
    
    prompt = f"""
Przeanalizuj poniższy tekst pod kątem SEO i linkowania wewnętrznego.
Twoim zadaniem jest znalezienie 8-15 fraz i słów kluczowych (np. nazwy modeli, technologie, nazwy systemów, typy urządzeń/maszyn, pojęcia branżowe), które DOSŁOWNIE lub PRAWIE DOSŁOWNIE występują w podanym tekście i stanowią idealne anchory pod linki wewnętrzne.

Oto rodzaje fraz, które MUSISZ wyciągnąć z tego tekstu:
1. Nazwy konkretnych modeli / produktów (np. "NOVACAT F 3100 OPTICURVE", "Kuhn GMD 15030", "Krone EasyCut B 1250 Fold")
2. Nazwy własne technologii/systemów (np. "Profiline", "ISOBUS", "ACTIVE FLOAT", "LIFT-CONTROL", "DSS")
3. Kategorie produktowe i opisy (np. "Kosiarki rolnicze do zielonek", "kosiarka z kondycjonerem", "sterowanie bocznego przesuwu", "kopiowanie podłoża", "kosiarka czołowa")

ZWRÓĆ WYNIK W FORMACIE TABELI Z KOLUMNAMI ROZDZIELONYMI ŚREDNIKIEM (;):
Fraza z tekstu;Proponowana tematyka linku;Uzasadnienie

Zasady:
- Każda fraza musi pochodzić z podanego tekstu!
- Zwróć dokładnie od 8 do 15 propozycji.
- ABSOLUTNY ZAKAZ dodawania wstępów, komentarzy czy nagłówków. Zwróć SAMĄ treść tabeli (linie rozdzielone średnikami)!

TEKST ARTYKUŁU:
{article_text[:12000]}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Jesteś analitykiem SEO i architektem informacji specjalizującym się w linkowaniu wewnętrznym."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )

    result_text = response.choices[0].message.content.strip()
    
    rows = []
    for line in result_text.split("\n"):
        line_clean = line.strip()
        if ";" in line_clean and not any(h in line_clean.lower() for h in ["fraza z tekstu", "proponowana tematyka"]):
            parts = line_clean.split(";")
            if len(parts) >= 3:
                rows.append({
                    "Fraza w tekście (Anchor)": parts[0].replace("`", "").replace("*", "").strip(),
                    "Tematyka docelowa": parts[1].strip(),
                    "Uzasadnienie": parts[2].strip()
                })
    return pd.DataFrame(rows)


# --- ANALIZA KROK 2: Dopasowywanie fraz do sitemapy przez AI ---
def match_keywords_to_sitemap(api_key, keywords_list, urls):
    client = OpenAI(api_key=api_key)
    
    urls_formatted = "\n".join(urls[:350])
    keywords_formatted = ", ".join(keywords_list)
    
    prompt = f"""
Twoim zadaniem jest dopasowanie poniższych fraz kluczowych do najbardziej pasujących adresów URL z sitemapy strony/sklepu.

LISTA WYKRYTYCH FRAZ Z TEKSTU:
{keywords_formatted}

LISTA ADRESÓW URL Z SITEMAPY:
{urls_formatted}

ZWRÓĆ WYNIK W FORMACIE TABELI Z KOLUMNAMI ROZDZIELONYMI ŚREDNIKIEM (;):
Fraza / Anchor;Rekomendowany URL;Uzasadnienie dopasowania

Zasady:
1. Dopasuj te adresy URL z sitemapy, które tematycznie lub słownie odpowiadają frazie (np. frazę 'NOVACAT F 3100' dopasuj do URL zawierającego tę nazwę, a frazę 'kosiarki rolnicze' do kafelka/kategorii z kosiarkami).
2. Jeśli dla danej frazy brak jakiegokolwiek logicznego odpowiednika w sitemapie, pomiń ją.
3. NIE PISZ żadnego wstępu ani podsumowania - zwróć wyłącznie linie danych rozdzielone średnikiem.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Jesteś ekspertem SEO ds. dopasowywania struktury URL i architektur linków."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )

    result_text = response.choices[0].message.content.strip()
    
    rows = []
    for line in result_text.split("\n"):
        line_clean = line.strip()
        if ";" in line_clean and not any(h in line_clean.lower() for h in ["fraza / anchor", "rekomendowany url"]):
            parts = line_clean.split(";")
            if len(parts) >= 3:
                rows.append({
                    "Sugerowany Anchor Text": parts[0].replace("`", "").replace("*", "").strip(),
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
            <p>Dwuetapowa analiza tekstu ze strukturą nagłówków i dopasowywanie adresów URL z sitemapy.</p>
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
        st.session_state.detected_keywords = None
        st.rerun()

    st.markdown("<h1>🔗 Linkowanie Wewnętrzne wspierane przez AI</h1>", unsafe_allow_html=True)

    # Sprawdzamy klucz API
    secret_key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if secret_key:
        api_key_input = secret_key
    else:
        api_key_input = st.sidebar.text_input("Klucz OpenAI API Key:", type="password")

    col1, col2 = st.columns([1, 1], gap="large")

    # --- LEWA KOLUMNA: KROK 1 ---
    with col1:
        st.subheader("1. Treść wpisu")
        input_type = st.radio("Sposób wprowadzania artykułu:", ["Wklej tekst ręcznie", "Pobierz z adresu URL"], horizontal=True)

        current_text = ""

        if input_type == "Wklej tekst ręcznie":
            current_text = st.text_area("Wklej tutaj tekst artykułu (może zawierać nagłówki i listy):", height=250, placeholder="Wpisz lub wklej treść...")
            if current_text:
                st.write("**Podgląd wprowadzonej treści:**")
                with st.container(height=400):
                    st.markdown(current_text)
        else:
            article_url = st.text_input("Adres URL wpisu:", placeholder="https://twojadomena.pl/moj-artykul", key="input_art_url")
            if article_url:
                st.session_state.article_url_val = article_url
                with st.spinner("Pobieranie i formatowanie treści ze strony..."):
                    fetched_text = extract_structured_text_from_url(article_url)
                    if fetched_text:
                        current_text = fetched_text
                        st.success(f"Pomyślnie pobrano i sformatowano treść ({len(current_text)} znaków).")
                        st.write("**Podgląd pobranej treści (ze strukturą nagłówków i list):**")
                        
                        with st.container(height=400):
                            st.markdown(current_text)
                    else:
                        st.error("Nie udało się pobrać treści z URL.")

        st.write("")
        analyze_step1_btn = st.button("🔍 Krok 1: Analizuj tekst i znajdź frazy do linkowania", type="primary", use_container_width=True)

        if analyze_step1_btn:
            if not api_key_input:
                st.error("Wprowadź Klucz OpenAI API!")
            elif not current_text.strip():
                st.error("Podaj treść artykułu lub poprawny link!")
            else:
                with st.spinner("AI analizuje sformatowaną treść pod kątem fraz kluczowych..."):
                    try:
                        st.session_state.article_text_saved = current_text
                        df_keywords = extract_keywords_with_ai(api_key_input, current_text)
                        st.session_state.detected_keywords = df_keywords
                        st.rerun()
                    except Exception as e:
                        st.error(f"Błąd analizy tekstu: {e}")

    # --- PRAWA KOLUMNA: KROK 2 I 3 ---
    with col2:
        st.subheader("2. Wykryte frazy przez AI")

        if st.session_state.detected_keywords is not None:
            if not st.session_state.detected_keywords.empty:
                st.success(f"✅ AI wytypowało {len(st.session_state.detected_keywords)} fraz z tekstu:")
                st.dataframe(st.session_state.detected_keywords, use_container_width=True)
            else:
                st.warning("⚠️ Nie udało się wyodrębnić jednoznacznych wyników. Spróbuj kliknąć analizę ponownie.")

            st.write("---")
            st.subheader("3. Dopasuj linki z Sitemapy")
            
            col_btn, col_info = st.columns([1, 1])
            with col_btn:
                fetch_robots_btn = st.button("🤖 Pobierz automatycznie z robots.txt")
            
            if fetch_robots_btn:
                target_domain = st.session_state.article_url_val
                if not target_domain:
                    st.warning("Najpierw podaj URL artykułu w Kroku 1 lub wklej bezpośredni adres domeny.")
                else:
                    with st.spinner("Sprawdzanie pliku robots.txt..."):
                        found_sitemap = get_sitemap_from_robots(target_domain)
                        if found_sitemap:
                            st.session_state.sitemap_url_val = found_sitemap
                            st.success("Znaleziono sitemapę w robots.txt!")
                        else:
                            st.error("Nie znaleziono ścieżki do sitemapy w pliku robots.txt.")

            sitemap_input = st.text_input(
                "Adres Sitemapy XML:", 
                value=st.session_state.sitemap_url_val,
                placeholder="https://twojadomena.pl/sitemap.xml",
                help="Możesz wkleić adres sitemapy ręcznie lub pobrać go automatycznie przyciskiem powyżej."
            )

            st.write("")
            match_step2_btn = st.button("🚀 Sprawdź i dopasuj linki z sitemapy", type="primary", use_container_width=True)

            if match_step2_btn:
                if not sitemap_input:
                    st.error("Wprowadź adres sitemapy XML!")
                else:
                    start_time = time.time()
                    
                    status_text = st.empty()
                    progress_bar = st.progress(0)
                    timer_text = st.empty()

                    try:
                        # 0% - Start pobierania sitemapy
                        status_text.markdown("**[1/2] Pobieranie i parsowanie sitemapy XML...**")
                        progress_bar.progress(10)
                        
                        def update_status(msg):
                            elapsed = int(time.time() - start_time)
                            timer_text.caption(f"⏱️ Czas trwania: {elapsed} sek.")
                            status_text.markdown(f"**[1/2] {msg}**")

                        urls = get_urls_from_sitemap(sitemap_input, progress_callback=update_status)
                        
                        # 50% - Pobrano sitemapę
                        progress_bar.progress(50)
                        elapsed = int(time.time() - start_time)
                        status_text.markdown(f"**[2/2] Dopasowywanie {len(urls)} adresów URL przez AI...**")
                        timer_text.caption(f"⏱️ Czas trwania: {elapsed} sek.")

                        kw_list = st.session_state.detected_keywords["Fraza w tekście (Anchor)"].tolist()

                        # 80% - Przetwarzanie AI
                        progress_bar.progress(80)
                        df_final = match_keywords_to_sitemap(api_key_input, kw_list, urls)

                        # 100% - Zakończono
                        progress_bar.progress(100)
                        total_elapsed = round(time.time() - start_time, 1)
                        
                        status_text.success(f" Gotowe! Zrealizowano w {total_elapsed} sek.")
                        timer_text.empty()

                        st.write("### 🎯 Gotowe dopasowania linków:")
                        if not df_final.empty:
                            # Konfiguracja tabeli z KLIKALNYMI LINKAMI
                            st.dataframe(
                                df_final,
                                use_container_width=True,
                                column_config={
                                    "Rekomendowany URL": st.column_config.LinkColumn(
                                        "Rekomendowany URL",
                                        help="Kliknij adres, aby otworzyć go w nowej karcie",
                                        validate="^https?://",
                                        display_text=r"https?://(?:www\.)?([^/]+)/?(.*)"
                                    )
                                }
                            )

                            csv_data = df_final.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Pobierz końcowy raport CSV",
                                data=csv_data,
                                file_name="gotowe_linkowanie_seo.csv",
                                mime="text/csv"
                            )
                        else:
                            st.warning("AI nie znalazło ścisłych dopasowań w sitemapie dla tych fraz.")

                    except Exception as e:
                        st.error(f"Błąd podczas dopasowywania sitemapy: {e}")
        else:
            st.info("👈 Najpierw wklej artykuł i kliknij 'Krok 1: Analizuj tekst', aby wygenerować propozycje fraz.")
