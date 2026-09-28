import streamlit as st

st.set_page_config(
    page_title="SEO Tools AI",
    page_icon="🤖",
    layout="wide"
)

st.markdown("""
    <h1>SEO Tools AI</h1>
    <p>Witaj w darmowym zestawie narzędzi SEO. Wybierz odpowiednie narzędzie poniżej lub skorzystaj z menu w panelu bocznym:</p>
    <hr style="margin: 20px 0;">
""", unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("""
    ### Linkowanie Wewnętrzne AI
    Narzędzie analizuje treść Twojego artykułu, wyciąga kluczowe frazy (anchory) i automatycznie dobiera najbardziej pasujące adresy URL z sitemapy za pomocą sztucznej inteligencji.
    """)
    st.write("")
    # Używamy st.page_link, żeby przycisk przenosił bezpośrednio do pliku w folderze pages/
    st.page_link("pages/linkowanie_wewnetrzne.py", label="Otwórz Linkowanie Wewnętrzne", icon="🔗", use_container_width=True)

with col2:
    st.markdown("""
    ### SEO Crawler i Audytor
    Szybki audytor podstron. Pozwala pobrać adresy automatycznie z sitemapy domeny lub wkleić listę ręcznie. Sprawdza statusy HTTP, przekierowania, Title, Meta Description, H1, Meta Robots oraz Canonical.
    """)
    st.write("")
    st.page_link("pages/seo_crawler.py", label="Otwórz SEO Crawler", icon="🕷️", use_container_width=True)
