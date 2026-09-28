import xml.etree.ElementTree as ET
import urllib.request
import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

st.set_page_config(page_title="Wykrywacz Linków 404", layout="wide")

st.markdown("<h1>🕷️ Szybki Weryfikator Linków 404 dla Sklepów i Stron</h1>", unsafe_allow_html=True)
st.caption("Narzędzie sprawdza listę adresów (lub sitemapę) i wykrywa wychodzące linki zwracające błąd 404.")

# Wybór źródła URL
source_type = st.radio("Skąd wziąć listę stron do sprawdzenia?", ["Z sitemapy XML", "Wklej listę adresów URL ręcznie"], horizontal=True)

urls_to_check = []

if source_type == "Z sitemapy XML":
    sitemap_url = st.text_input("Podaj adres Sitemapy XML:", placeholder="https://twojadomena.pl/sitemap.xml")
    if st.button("Pobierz adresy z sitemapy"):
        if sitemap_url:
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                resp = requests.get(sitemap_url, headers=headers, timeout=10)
                root = ET.fromstring(resp.content)
                found = [elem.text.strip() for elem in root.iter() if elem.tag.endswith('loc') and elem.text]
                st.session_state.sitemap_urls = found
                st.success(f"Pobrano {len(found)} adresów URL z sitemapy.")
            except Exception as e:
                st.error(f"Błąd pobierania sitemapy: {e}")
        else:
            st.warning("Podaj adres sitemapy.")
            
    if "sitemap_urls" in st.session_state:
        urls_to_check = st.session_state.sitemap_urls
        st.write(f"Łącznie gotowych do skanowania: **{len(urls_to_check)}** adresów.")
else:
    manual_input = st.text_area("Wklej adresy URL (każdy w nowej linii):", height=200)
    if manual_input:
        urls_to_check = [u.strip() for u in manual_input.splitlines() if u.strip()]

st.markdown("---")
# Opcja e-commerce
skip_products_on_categories = st.checkbox(
    "🛒 Sklep internetowy: Na stronach kategorii pomijaj linki prowadzące do produktów", 
    value=True
)

def check_link_status(url):
    try:
        resp = requests.head(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5, allow_redirects=True)
        # Jeśli serwer nie obsługuje HEAD, spróbuj GET
        if resp.status_code >= 400:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5, allow_redirects=True)
        return resp.status_code
    except requests.Timeout:
        return "Timeout"
    except Exception:
        return "Błąd połączenia"

def audit_site_for_404(pages_list, skip_prods):
    broken_links = []
    headers = {"User-Agent": "Mozilla/5.0"}
    
    category_indicators = ['/c/', '/kategoria/', '/kolekcja/', '/katalog/', '/shop/']
    product_indicators = ['/p/', '-p-', '/produkt/', '/product/', '/towar/']

    progress_bar = st.progress(0)
    status_text = st.empty()
    
    pages_to_scan = pages_list[:100]  # Ograniczenie do 100 stron dla bezpieczeństwa
    
    for idx, page_url in enumerate(pages_to_scan):
        status_text.markdown(f"Skanowanie strony ({idx+1}/{len(pages_to_scan)}): `{page_url}`")
        progress_bar.progress((idx + 1) / len(pages_to_scan))
        
        try:
            resp = requests.get(page_url, headers=headers, timeout=8)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                parsed_base = urlparse(page_url)
                domain = parsed_base.netloc
                
                is_category_page = any(ind in page_url.lower() for ind in category_indicators)
                
                internal_links = set()
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    full_url = urljoin(page_url, href)
                    parsed_full = urlparse(full_url)
                    
                    if parsed_full.netloc == domain and '#' not in parsed_full.path:
                        clean_link = full_url.split('#')[0]
                        
                        if skip_prods and is_category_page:
                            if any(prod_ind in clean_link.lower() for prod_ind in product_indicators):
                                continue

                        internal_links.add(clean_link)
                        
                # Sprawdzanie linków ze strony (max 20 linków na stronę)
                for link in list(internal_links)[:20]:
                    status = check_link_status(link)
                    if status in [404, 410, "Timeout", "Błąd połączenia"]:
                        broken_links.append({
                            "Strona źródłowa": page_url,
                            "Sprawdzany link": link,
                            "Status HTTP": status
                        })
        except Exception:
            continue
            
    status_text.empty()
    progress_bar.empty()
    return pd.DataFrame(broken_links)

if st.button("🚀 Rozpocznij audyt linków 404", type="primary"):
    if not urls_to_check:
        st.warning("Najpierw wklej lub pobierz listę adresów URL.")
    else:
        with st.spinner("Trwa skanowanie..."):
            df_broken = audit_site_for_404(urls_to_check, skip_products_on_categories)
            
            st.write("### Wyniki audytu martwych linków:")
            if not df_broken.empty:
                st.error(f"Znaleziono **{len(df_broken)}** potencjalnych błędów!")
                st.dataframe(df_broken, use_container_width=True)
                
                csv_data = df_broken.to_csv(index=False).encode('utf-8')
                st.download_button("Pobierz raport 404 (CSV)", data=csv_data, file_name="raport_404.csv", mime="text/csv")
            else:
                st.success("🎉 Super! Nie znaleziono żadnych linków prowadzących do błędów 404 na przeskanowanych podstronach.")
