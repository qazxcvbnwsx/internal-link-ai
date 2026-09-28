import xml.etree.ElementTree as ET
import urllib.request
import urllib.error
import time
import pandas as pd
import streamlit as st
from urllib.parse import urlparse
from html.parser import HTMLParser

st.set_page_config(page_title="SEO Crawler i Audytor", layout="wide")

if "crawled_urls_list" not in st.session_state:
    st.session_state.crawled_urls_list = []

IGNORED_EXTENSIONS = (
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.ico',
    '.pdf', '.zip', '.rar', '.doc', '.docx', '.xls', '.xlsx', '.mp3', '.mp4'
)

class SEOCrawlerParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.meta_desc = ""
        self.h1_list = []
        self.meta_robots = ""
        self.canonical = ""
        self._in_title = False
        self._in_h1 = False
        self._current_h1 = []

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        attrs_dict = dict(attrs)
        if tag_lower == 'title':
            self._in_title = True
        elif tag_lower == 'h1':
            self._in_h1 = True
            self._current_h1 = []
        elif tag_lower == 'meta':
            name = attrs_dict.get('name', '').lower()
            content = attrs_dict.get('content', '')
            if name == 'description':
                self.meta_desc = content.strip()
            elif name == 'robots':
                self.meta_robots = content.strip()
        elif tag_lower == 'link':
            rel = attrs_dict.get('rel', '').lower()
            if 'canonical' in rel:
                self.canonical = attrs_dict.get('href', '').strip()

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._in_h1:
            self._current_h1.append(data)

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower == 'title':
            self.title = self.title.strip()
            self._in_title = False
        elif tag_lower == 'h1':
            h1_text = "".join(self._current_h1).strip()
            if h1_text:
                self.h1_list.append(h1_text)
            self._in_h1 = False

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

def fetch_and_parse_xml(url):
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/xml;q=0.9,*/*;q=0.8"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as response:
        xml_data = response.read()
    return ET.fromstring(xml_data)

def get_urls_from_sitemap(url):
    visited = set()
    urls = []
    try:
        root = fetch_and_parse_xml(url)
    except Exception:
        return urls
    
    sub_sitemaps = []
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
                urls.append(loc)
    return list(dict.fromkeys(urls))

st.markdown("<h1>SEO Crawler i Audytor stron</h1>", unsafe_allow_html=True)

crawler_source = st.radio("Źródło adresów URL:", ["Podaj domenę (automatyczna sitemapa)", "Wklej listę URL ręcznie"], horizontal=True)

if crawler_source == "Podaj domenę (automatyczna sitemapa)":
    domain_input = st.text_input("Podaj domenę lub adres URL:", placeholder="https://twojadomena.pl")
    if st.button("Pobierz adresy z sitemapy"):
        if not domain_input:
            st.error("Podaj domenę!")
        else:
            with st.spinner("Pobieranie sitemapy..."):
                found_sitemap = get_sitemap_from_robots(domain_input)
                if not found_sitemap:
                    parsed_d = urlparse(domain_input)
                    base = f"{parsed_d.scheme}://{parsed_d.netloc}" if parsed_d.netloc else f"https://{domain_input}"
                    found_sitemap = f"{base}/sitemap.xml"
                
                try:
                    fetched = get_urls_from_sitemap(found_sitemap)
                    st.session_state.crawled_urls_list = fetched
                    st.success(f"Pobrano {len(fetched)} adresów URL!")
                except Exception as e:
                    st.error(f"Błąd: {e}")
    
    if st.session_state.crawled_urls_list:
        st.info(f"Gotowych do audytu: **{len(st.session_state.crawled_urls_list)}** adresów.")

else:
    manual_urls_text = st.text_area("Wklej adresy URL (każdy w nowej linii):", height=150)
    if manual_urls_text:
        st.session_state.crawled_urls_list = [u.strip() for u in manual_urls_text.splitlines() if u.strip()]
        st.info(f"Wprowadzono ręcznie **{len(st.session_state.crawled_urls_list)}** adresów.")

st.markdown("---")
st.subheader("2. Wybierz parametry do sprawdzenia:")

col1, col2, col3, col4 = st.columns(4)
with col1:
    chk_status = st.checkbox("Status HTTP", value=True)
    chk_redirects = st.checkbox("Przekierowania", value=True)
with col2:
    chk_title = st.checkbox("Title (Meta Tytuł)", value=True)
    chk_desc = st.checkbox("Meta Description", value=True)
with col3:
    chk_h1 = st.checkbox("H1 (ilość i treść)", value=True)
    chk_robots = st.checkbox("Meta Robots", value=True)
with col4:
    chk_canonical = st.checkbox("Canonical", value=True)

if st.button("Uruchom Audyt SEO", type="primary"):
    urls_to_crawl = st.session_state.get("crawled_urls_list", [])
    if not urls_to_crawl:
        st.error("Brak adresów URL do sprawdzenia!")
    else:
        audit_results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        total = len(urls_to_crawl)

        for idx, url in enumerate(urls_to_crawl):
            progress_bar.progress(int(((idx + 1) / total) * 100))
            status_text.markdown(f"**Sprawdzam ({idx+1}/{total}):** `{url}`")
            row_data = {"URL": url}
            
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=8) as response:
                    final_url = response.url
                    status_code = response.code
                    html_content = response.read().decode('utf-8', errors='ignore')
                
                if chk_status:
                    row_data["Status HTTP"] = status_code
                if chk_redirects:
                    row_data["Przekierowanie"] = f"Tak -> {final_url}" if final_url.rstrip('/') != url.rstrip('/') else "Brak (200 OK)"

                parser = SEOCrawlerParser()
                parser.feed(html_content)

                if chk_title:
                    row_data["Title"] = parser.title
                if chk_desc:
                    row_data["Meta Description"] = parser.meta_desc
                if chk_h1:
                    row_data["Liczba H1"] = len(parser.h1_list)
                    row_data["Treść H1"] = " | ".join(parser.h1_list)
                if chk_robots:
                    row_data["Meta Robots"] = parser.meta_robots if parser.meta_robots else "index, follow"
                if chk_canonical:
                    row_data["Canonical"] = parser.canonical if parser.canonical else "Brak"

            except Exception as e:
                if chk_status: row_data["Status HTTP"] = "Błąd"
                if chk_title: row_data["Title"] = str(e)

            audit_results.append(row_data)

        progress_bar.progress(100)
        status_text.success("Audyt zakończony!")
        df_audit = pd.DataFrame(audit_results)
        st.dataframe(df_audit, use_container_width=True)

        csv_data = df_audit.to_csv(index=False).encode('utf-8')
        st.download_button("Pobierz raport CSV", data=csv_data, file_name="seo_audit.csv", mime="text/csv")
