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
            text = trafilatura.extract(downloaded, output_format='markdown', include_formatting=True, include_links=False)
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
Znajdź 8-15 fraz i słów kluczowych, które DOSŁOWNIE lub PRAWIE DOSŁOWNIE występują w tekście i stanowią idealne anchory.
ZWRÓĆ WYNIK W FORMACIE TABELI Z KOLUMNAMI ROZDZIELONYMI ŚREDNIKIEM (;):
Fraza z tekstu;Proponowana tematyka linku;Uzasadnienie
Zasady: Brak wstępów, tylko wiersze tabeli.
TEKST:
{article_text[:12000]}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "Jesteś analitykiem SEO."}, {"role": "user", "content": prompt}],
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

def match_keywords_to_sitemap(api_key, keywords_list, urls):
    client = OpenAI(api_key=api_key)
    urls_formatted = "\n".join(urls[:350])
    keywords_formatted = ", ".join(keywords_list)
    prompt = f"""
Dopasuj poniższe frazy kluczowe do adresów URL z sitemapy.
FRAZY: {keywords_formatted}
URL-E: {urls_formatted}
ZWRÓĆ WYNIK W FORMACIE TABELI Z KOLUMNAMI ROZDZIELONYMI ŚREDNIKIEM (;):
Fraza / Anchor;Rekomendowany Pełny URL;Uzasadnienie dopasowania
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "Jesteś ekspertem SEO."}, {"role": "user", "content": prompt}],
        temperature=0.1
    )
    result_text = response.choices[0].message.content.strip()
    rows = []
    for line in result_text.split("\n"):
        line_clean = line.strip()
        if ";" in line_clean and not any(h in line_clean.lower() for h in ["fraza / anchor", "rekomendowany pełny url"]):
            parts = line_clean.split(";")
            if len(parts) >= 3:
                rows.append({
                    "Fraza / Anchor z tekstu": parts[0].replace("`", "").replace("*", "").strip(),
                    "Rekomendowany Pełny URL": parts[1].strip(),
                    "Uzasadnienie AI": parts[2].strip()
                })
    return pd.DataFrame(rows)

st.markdown("<h1>Linkowanie Wewnętrzne AI</h1>", unsafe_allow_html=True)

secret_key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
if secret_key:
    api_key_input = secret_key
else:
    api_key_input = st.sidebar.text_input("Klucz OpenAI API Key:", type="password")

st.markdown("---")
st.subheader("1. Treść wpisu")
input_type = st.radio("Sposób wprowadzania artykułu:", ["Wklej tekst ręcznie", "Pobierz z adresu URL"], horizontal=True)

current_text = ""
if input_type == "Wklej tekst ręcznie":
    current_text = st.text_area("Wklej tutaj tekst artykułu:", height=220)
else:
    article_url = st.text_input("Adres URL wpisu:", placeholder="https://twojadomena.pl/moj-artykul")
    if article_url:
        st.session_state.article_url_val = article_url
        with st.spinner("Pobieranie treści..."):
            fetched_text = extract_structured_text_from_url(article_url)
            if fetched_text:
                current_text = fetched_text
                st.success(f"Pobrano treść ({len(current_text)} znaków).")

if st.button("Krok 1: Analizuj tekst i znajdź frazy do linkowania", type="primary"):
    if not api_key_input:
        st.error("Wprowadź Klucz OpenAI API!")
    elif not current_text.strip():
        st.error("Podaj treść artykułu lub link!")
    else:
        with st.spinner("Analizowanie tekstu przez AI..."):
            df_keywords = extract_keywords_with_ai(api_key_input, current_text)
            st.session_state.detected_keywords = df_keywords
            st.success("Zakończono analizę tekstu!")
            st.rerun()

if st.session_state.detected_keywords is not None and not st.session_state.detected_keywords.empty:
    st.markdown("---")
    st.subheader("2. Wykryte frazy przez AI")
    st.dataframe(st.session_state.detected_keywords, use_container_width=True)

    st.markdown("---")
    st.subheader("3. Dopasuj linki z Sitemapy")
    
    if st.button("Pobierz sitemapę z robots.txt"):
        if st.session_state.article_url_val:
            found_sitemap = get_sitemap_from_robots(st.session_state.article_url_val)
            if found_sitemap:
                st.session_state.sitemap_url_val = found_sitemap
                st.success("Znaleziono sitemapę!")
            else:
                st.error("Nie znaleziono sitemapy w robots.txt.")

    sitemap_input = st.text_input("Adres Sitemapy XML:", value=st.session_state.sitemap_url_val)

    if st.button("Krok 2: Dopasuj linki z sitemapy", type="primary"):
        if not sitemap_input:
            st.error("Wprowadź adres sitemapy!")
        else:
            with st.spinner("Pobieranie sitemapy i dopasowywanie linków przez AI..."):
                raw_urls = get_urls_from_sitemap(sitemap_input)
                kw_list = st.session_state.detected_keywords["Fraza w tekście (Anchor)"].tolist()
                df_final = match_keywords_to_sitemap(api_key_input, kw_list, raw_urls)
                
                if not df_final.empty:
                    st.success("Gotowe!")
                    st.dataframe(df_final, use_container_width=True)
                    csv_data = df_final.to_csv(index=False).encode('utf-8')
                    st.download_button("Pobierz raport CSV", data=csv_data, file_name="linkowanie.csv", mime="text/csv")
                else:
                    st.warning("Brak dopasowań.")
