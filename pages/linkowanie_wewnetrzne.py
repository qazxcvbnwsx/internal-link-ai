import os
import xml.etree.ElementTree as ET
import urllib.request
import time
import json
import pandas as pd
import streamlit as st
import trafilatura
from urllib.parse import urlparse

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

st.set_page_config(page_title="Linkowanie Wewnętrzne AI", layout="wide")

if "detected_keywords" not in st.session_state:
    st.session_state.detected_keywords = None
if "article_text_saved" not in st.session_state:
    st.session_state.article_text_saved = ""
if "sitemap_url_val" not in st.session_state:
    st.session_state.sitemap_url_val = ""
if "article_url_val" not in st.session_state:
    st.session_state.article_url_val = ""

IGNORED_EXTENSIONS = (
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.ico',
    '.pdf', '.zip', '.rar', '.doc', '.docx', '.xls', '.xlsx', '.mp3', '.mp4'
)

def get_sitemap_from_robots(url_or_domain):
    try:
        parsed = urlparse(url_or_domain)
        scheme = parsed.scheme if parsed.scheme else "https"
        netloc = parsed.netloc if parsed.netloc else parsed.path.split('/')[0]
        if not netloc:
            return None
        robots_url = f"{scheme}://{netloc}/robots.txt"
        req = urllib.request.Request(robots_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            content = response.read().decode('utf-8', errors='ignore')
        for line in content.splitlines():
            if line.strip().lower().startswith("sitemap:"):
                return line.split(":", 1)[1].strip()
        return None
    except Exception:
        return None

def extract_structured_text_from_url(url):
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, output_format='markdown', include_formatting=True, include_links=True)
            if text:
                return text
        return None
    except Exception as e:
        st.error(f"Błąd podczas pobierania treści z URL: {e}")
        return None

def fetch_and_parse_xml(url):
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/xml;q=0.9,*/*;q=0.8"}
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
            loc_lower = loc.lower()
            if loc_lower.endswith(IGNORED_EXTENSIONS):
                continue
            if loc_lower.endswith('.xml') or 'sitemap' in loc_lower:
                if 'image' not in loc_lower and 'photo' not in loc_lower:
                    sub_sitemaps.append(loc)
            else:
                page_urls.append(loc)
    urls.extend(page_urls)
    total_state["count"] += len(page_urls)
    if progress_callback:
        progress_callback(f"Pobrano {total_state['count']} URL-i...")
    for sub_url in sub_sitemaps:
        if sub_url not in visited:
            urls.extend(get_urls_from_sitemap(sub_url, progress_callback, visited, total_state))
    return list(dict.fromkeys(urls))

def extract_keywords_with_ai(api_key, article_text):
    client = OpenAI(api_key=api_key)
    
    prompt = f"""
Przeanalizuj poniższy tekst pod kątem SEO i linkowania wewnętrznego.
Tekst zawiera już pewne linki w formacie Markdown np. [tekst_linku](url_docelowy).
Twoim zadaniem jest znalezienie maksymalnie 20 konkretnych fraz i słów kluczowych (np. "otulacze", "kocyki", "kombinezony"), które stanowią świetne anchory do linkowania.
Dla każdej frazy określ jej status linkowania (jeśli ma już link w tekście, podaj go, w przeciwnym razie wpisz "brak linku").

Zwróć odpowiedź WYŁĄCZNIE w formacie JSON o następującej strukturze:
[
  {{"anchor": "fraza 1", "status": "brak linku"}},
  {{"anchor": "fraza 2", "status": "https://domena.pl/istniejacy-link"}}
]

TEKST:
{article_text[:12000]}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "Jesteś analitykiem SEO. Zwracasz wyłącznie poprawny sformatowany JSON."}, {"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1
    )
    
    try:
        content = response.choices[0].message.content
        data = json.loads(content)
        # Obsługa różnych wariantów kluczy w zablokowanym formacie json
        items = data if isinstance(data, list) else data.get("items", data.get("phrases", data.get("keywords", [])))
        if not items and isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, list):
                    items = v
                    break

        rows = []
        for item in items:
            if isinstance(item, dict):
                anchor = item.get("anchor", item.get("Fraza", ""))
                status = item.get("status", item.get("Status", "brak linku"))
                if anchor:
                    rows.append({
                        "Fraza w tekście (Anchor)": anchor.strip(),
                        "Status linkowania": status.strip() if status else "brak linku"
                    })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame(columns=["Fraza w tekście (Anchor)", "Status linkowania"])

def match_keywords_to_sitemap(api_key, keywords_list, urls, is_ecommerce):
    client = OpenAI(api_key=api_key)
    urls_formatted = "\n".join(urls[:400])
    keywords_json = json.dumps(keywords_list, ensure_ascii=False)
    
    ecommerce_instruction = ""
    if is_ecommerce:
        ecommerce_instruction = """
ZASADA DLA SKLEPU INTERNETOWEGO:
- Wybieraj PREFERENCYJNIE adresy URL będące kategoriami (np. zawierające /c/, /kategoria/, /kolekcja/) lub stronami zbiorczymi.
- UNIKAJ pojedynczych produktów lub zestawów ubranek, jeśli dla danej frazy (np. "otulacze") istnieje w sitemapie dedykowana kategoria nadrzędna.
"""

    prompt = f"""
Dopasuj poniższą listę fraz kluczowych do najlepszych adresów URL z listy sitemapy.

LISTA FRAZ DO DOPASOWANIA:
{keywords_json}

LISTA URL Z SITEMAPY:
{urls_formatted}

{ecommerce_instruction}

Zwróć odpowiedź WYŁĄCZNIE w formacie JSON o następującej strukturze listy obiektów:
[
  {{"anchor": "dokładna fraza", "url": "pełny adres https://...", "reason": "uzasadnienie wyboru"}},
  ...
]
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "Jesteś ekspertem SEO architektury linków. Zwracasz wyłącznie czysty JSON."}, {"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.0
    )
    
    try:
        content = response.choices[0].message.content
        data = json.loads(content)
        items = data if isinstance(data, list) else data.get("matches", data.get("results", data.get("links", [])))
        if not items and isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, list):
                    items = v
                    break

        rows = []
        for item in items:
            if isinstance(item, dict):
                anchor = item.get("anchor", item.get("Fraza", ""))
                url = item.get("url", item.get("URL", ""))
                reason = item.get("reason", item.get("Uzasadnienie", ""))
                if anchor and url:
                    rows.append({
                        "Fraza / Anchor z tekstu": anchor.strip(),
                        "Rekomendowany Pełny URL": url.strip(),
                        "Uzasadnienie AI": reason.strip()
                    })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame(columns=["Fraza / Anchor z tekstu", "Rekomendowany Pełny URL", "Uzasadnienie AI"])

st.markdown("<h1>Linkowanie Wewnętrzne AI</h1>", unsafe_allow_html=True)

secret_key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
if secret_key:
    api_key_input = secret_key
else:
    api_key_input = st.sidebar.text_input("Klucz OpenAI API Key:", type="password")

# --- KROK 1: TREŚĆ WPISU ---
st.markdown("---")
st.subheader("1. Treść wpisu")
input_type = st.radio("Sposób wprowadzania artykułu:", ["Wklej tekst ręcznie", "Pobierz z adresu URL"], horizontal=True)

current_text = ""
if input_type == "Wklej tekst ręcznie":
    current_text = st.text_area("Wklej tutaj tekst artykułu:", height=220)
    if current_text:
        st.write("**Podgląd wprowadzonej treści:**")
        with st.container(height=300):
            st.markdown(current_text)
else:
    article_url = st.text_input("Adres URL wpisu:", placeholder="https://twojadomena.pl/moj-artykul")
    if article_url:
        st.session_state.article_url_val = article_url
        with st.spinner("Pobieranie treści wraz z istniejącymi linkami..."):
            fetched_text = extract_structured_text_from_url(article_url)
            if fetched_text:
                current_text = fetched_text
                st.success(f"Pobrano treść wraz z linkami ({len(current_text)} znaków).")
                st.write("**Podgląd pobranej treści:**")
                with st.container(height=300):
                    st.markdown(current_text)
            else:
                st.error("Nie udało się pobrać treści z URL.")

st.write("")
analyze_step1_btn = st.button("Krok 1: Analizuj tekst i sprawdź obecne linki", type="primary")

if analyze_step1_btn:
    if not api_key_input:
        st.error("Wprowadź Klucz OpenAI API!")
    elif not current_text.strip():
        st.error("Podaj treść artykułu lub link!")
    else:
        start_time_step1 = time.time()
        status_text_1 = st.empty()
        progress_bar_1 = st.progress(0)
        timer_text_1 = st.empty()

        try:
            status_text_1.markdown("**[1/2] Skanowanie treści i istniejących linków w tekście...**")
            progress_bar_1.progress(20)
            
            st.session_state.article_text_saved = current_text

            status_text_1.markdown("**[2/2] Analiza AI (strukturalny JSON): wykrywanie fraz...**")
            progress_bar_1.progress(60)

            df_keywords = extract_keywords_with_ai(api_key_input, current_text)
            
            progress_bar_1.progress(100)
            status_text_1.success("Zakończono analizę tekstu i linków!")
            timer_text_1.empty()

            st.session_state.detected_keywords = df_keywords
            st.rerun()

        except Exception as e:
            status_text_1.empty()
            progress_bar_1.empty()
            timer_text_1.empty()
            st.error(f"Błąd analizy tekstu: {e}")

# --- KROK 2 I 3: WYKRYTE FRAZY ORAZ SITEMAPA ---
if st.session_state.detected_keywords is not None:
    st.markdown("---")
    st.subheader("2. Wybierz frazy do linkowania")
    st.write("Zaznacz interesujące Cię frazy.")

    if not st.session_state.detected_keywords.empty:
        with st.form("keywords_selection_form"):
            checkbox_states = {}
            
            c_head1, c_head2, c_head3 = st.columns([1, 4, 3])
            c_head1.markdown("**Wybierz**")
            c_head2.markdown("**Fraza w tekście (Anchor)**")
            c_head3.markdown("**Status linkowania**")
            st.write("")

            for idx, row in st.session_state.detected_keywords.iterrows():
                col1, col2, col3 = st.columns([1, 4, 3])
                
                saved_states = st.session_state.get("saved_checkbox_states", {})
                default_val = saved_states.get(row["Fraza w tekście (Anchor)"], False)

                is_checked = col1.checkbox("", key=f"chk_{idx}", value=default_val)
                checkbox_states[row["Fraza w tekście (Anchor)"]] = is_checked
                
                col2.write(row["Fraza w tekście (Anchor)"])
                
                status_val = row["Status linkowania"]
                if status_val.startswith("http"):
                    col3.markdown(f"[{status_val}]({status_val})")
                else:
                    col3.write(status_val)

            st.write("")
            submit_selection = st.form_submit_button("Zatwierdź zaznaczone frazy", type="primary")
            
            if submit_selection:
                selected_keywords_list = [phrase for phrase, checked in checkbox_states.items() if checked]
                st.session_state.temp_selected_keywords = selected_keywords_list
                st.session_state.saved_checkbox_states = checkbox_states
                
                if selected_keywords_list:
                    st.success(f"✅ Zatwierdzono! Wybrano {len(selected_keywords_list)} fraz do analizy w Kroku 3.")
                else:
                    st.warning("⚠️ Nie zaznaczono żadnej frazy.")
    else:
        st.warning("Nie znaleziono wyników.")

    st.markdown("---")
    st.subheader("3. Dopasuj nowe linki z Sitemapy")
    
    is_ecommerce_site = st.checkbox(
        "Mam sklep internetowy (szukaj w sitemapie przede wszystkim kategorii np. 'otulacze', 'kocyki')", 
        value=True
    )

    col_btn, _ = st.columns([1, 2])
    with col_btn:
        fetch_robots_btn = st.button("Pobierz automatycznie sitemapę z robots.txt", use_container_width=True)
    
    if fetch_robots_btn:
        target_domain = st.session_state.article_url_val
        if not target_domain:
            st.warning("Najpierw podaj URL artykułu w Kroku 1.")
        else:
            with st.spinner("Sprawdzanie pliku robots.txt..."):
                found_sitemap = get_sitemap_from_robots(target_domain)
                if found_sitemap:
                    st.session_state.sitemap_url_val = found_sitemap
                    st.success("Znaleziono sitemapę w robots.txt!")
                else:
                    st.error("Nie znaleziono ścieżki do sitemapy w robots.txt.")

    sitemap_input = st.text_input(
        "Adres Sitemapy XML:", 
        value=st.session_state.sitemap_url_val,
        placeholder="https://twojadomena.pl/sitemap.xml"
    )

    with st.expander("Zaawansowane filtry URL-i z sitemapy (opcjonalnie)", expanded=False):
        col_inc, col_exc = st.columns(2)
        with col_inc:
            include_filter = st.text_input("Musi zawierać w URL:", value="", placeholder="np. /c/, /kategoria/")
        with col_exc:
            exclude_filter = st.text_input("Wyklucz z URL:", value="", placeholder="np. /p/, /tag/")

    st.write("")
    match_step2_btn = st.button("Krok 3: Szukaj i dopasuj linki dla zaznaczonych fraz", type="primary", use_container_width=True)

    if match_step2_btn:
        final_selected = st.session_state.get("temp_selected_keywords", [])
        
        if not final_selected:
            st.warning("Nie zaznaczono żadnej frazy! Zaznacz ptaszkami pozycje powyżej i kliknij 'Zatwierdź zaznaczone frazy'.")
        elif not sitemap_input:
            st.error("Wprowadź adres sitemapy XML!")
        else:
            start_time = time.time()
            status_text = st.empty()
            progress_bar = st.progress(0)

            try:
                status_text.markdown("**[1/3] Pobieranie i parsowanie sitemapy XML...**")
                progress_bar.progress(10)
                
                raw_urls = get_urls_from_sitemap(sitemap_input)
                
                progress_bar.progress(40)
                filtered_urls = raw_urls
                
                if include_filter.strip():
                    inc_patterns = [p.strip().lower() for p in include_filter.split(",") if p.strip()]
                    filtered_urls = [u for u in filtered_urls if any(p in u.lower() for p in inc_patterns)]
                    
                if exclude_filter.strip():
                    exc_patterns = [p.strip().lower() for p in exclude_filter.split(",") if p.strip()]
                    filtered_urls = [u for u in filtered_urls if not any(p in u.lower() for p in exc_patterns)]

                st.info(f"Po przefiltrowaniu pozostało {len(filtered_urls)} adresów URL stron.")

                progress_bar.progress(60)
                status_text.markdown("**[3/3] Dopasowywanie nowych adresów URL przez AI (tryb JSON)...**")

                df_final = match_keywords_to_sitemap(api_key_input, final_selected, filtered_urls, is_ecommerce_site)

                progress_bar.progress(100)
                status_text.success("Gotowe!")

                st.write("### Gotowe propozycje nowych linków:")
                if not df_final.empty:
                    st.dataframe(
                        df_final,
                        use_container_width=True,
                        column_config={
                            "Rekomendowany Pełny URL": st.column_config.LinkColumn(
                                "Rekomendowany Pełny URL",
                                help="Kliknij pełny adres URL, aby otworzyć go w nowej karcie"
                            )
                        }
                    )

                    csv_data = df_final.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Pobierz końcowy raport CSV",
                        data=csv_data,
                        file_name="nowe_linkowanie_seo.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("AI nie znalazło dopasowań lub zwróciło pustą strukturę dla zaznaczonych fraz.")

            except Exception as e:
                status_text.empty()
                progress_bar.empty()
                st.error(f"Błąd podczas dopasowywania sitemapy: {e}")
