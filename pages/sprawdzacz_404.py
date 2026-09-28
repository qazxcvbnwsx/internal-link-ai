import asyncio
import aiohttp
import xml.etree.ElementTree as ET
import urllib.request
import pandas as pd
import streamlit as st
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
                req = urllib.request.Request(sitemap_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    xml_data = resp.read()
                root = ET.fromstring(xml_data)
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
    "🛒 Sklep internetowy: Na stronach kategorii pomijaj linki prowadzące do produktów (przyspiesza skanowanie i skupia się na menu/stopce/treści)", 
    value=True
)


# Funkcja asynchroniczna do sprawdzania pojedynczego linku
async def check_single_link(session, source_page, link_url):
    try:
        async with session.get(link_url, timeout=7, allow_redirects=True) as response:
            status = response.status
            return {"Strona źródłowa": source_page, "Sprawdzany link": link_url, "Status HTTP": status}
    except asyncio.TimeoutError:
        return {"Strona źródłowa": source_page, "Sprawdzany link": link_url, "Status HTTP": "Timeout"}
    except Exception:
        return {"Strona źródłowa": source_page, "Sprawdzany link": link_url, "Status HTTP": "Błąd połączenia"}


# Główna funkcja skanująca podstrony
async def audit_site_for_404(pages_list, skip_prods):
    broken_links = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    # Wzorce po których rozpoznamy czy dany URL to podstrona kategorii w sklepie
    category_indicators = ['/c/', '/kategoria/', '/kolekcja/', '/katalog/', '/shop/']
    # Wzorce po których rozpoznamy linki do pojedynczych produktów
    product_indicators = ['/p/', '-p-', '/produkt/', '/product/', '/towar/']

    async with aiohttp.ClientSession(headers=headers) as session:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Limit do 150 stron dla bezpieczeństwa zasobów
        pages_to_scan = pages_list[:150]
        
        for idx, page_url in enumerate(pages_to_scan):
            status_text.markdown(f"Skanowanie strony ({idx+1}/{len(pages_to_scan)}): `{page_url}`")
            progress_bar.progress((idx + 1) / len(pages_to_scan))
            
            try:
                async with session.get(page_url, timeout=8) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        parsed_base = urlparse(page_url)
                        domain = parsed_base.netloc
                        
                        # Sprawdzamy czy obecna strona to kategoria
                        is_category_page = any(ind in page_url.lower() for ind in category_indicators)
                        
                        internal_links = set()
                        for a_tag in soup.find_all('a', href=True):
                            href = a_tag['href']
                            full_url = urljoin(page_url, href)
                            parsed_full = urlparse(full_url)
                            
                            # Tylko linki wewnętrzne, bez kotwic (#) i plików graficznych/pdf
                            if parsed_full.netloc == domain and '#' not in parsed_full.path:
                                clean_link = full_url.split('#')[0]
                                
                                # Jeśli włączone jest pomijanie produktów na kategoriach
                                if skip_prods and is_category_page:
                                    if any(prod_ind in clean_link.lower() for prod_ind in product_indicators):
                                        continue # Pomijamy link do produktu na stronie kategorii!

                                internal_links.add(clean_link)
                                
                        # Sprawdzanie statusów znalezionych linków asynchronicznie (max 25 linków ze strony)
                        tasks = [check_single_link(session, page_url, link) for link in list(internal_links)[:25]]
                        results = await asyncio.gather(*tasks)
                        
                        for res in results:
                            if res["Status HTTP"] in [404, 410, "Timeout", "Błąd połączenia"]:
                                broken_links.append(res)
            except Exception:
                continue
                
        status_text.empty()
        progress_bar.empty()
        
    return pd.DataFrame(broken_links)


if st.button("🚀 Rozpocznij audyt linków 404", type="primary"):
    if not urls_to_check:
        st.warning("Najpierw wklej lub pobierz listę adresów URL.")
    else:
        with st.spinner("Trwa błyskawiczne skanowanie asynchroniczne..."):
            df_broken = asyncio.run(audit_site_for_404(urls_to_check, skip_products_on_categories))
            
            st.write("### Wyniki audytu martwych linków:")
            if not df_broken.empty:
                st.error(f"Znaleziono **{len(df_broken)}** potencjalnych błędów!")
                st.dataframe(df_broken, use_container_width=True)
                
                csv_data = df_broken.to_csv(index=False).encode('utf-8')
                st.download_button("Pobierz raport 404 (CSV)", data=csv_data, file_name="raport_404.csv", mime="text/csv")
            else:
                st.success("🎉 Super! Nie znaleziono żadnych linków prowadzących do błędów 404 na przeskanowanych podstronach.")
