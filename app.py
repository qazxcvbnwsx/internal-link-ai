import streamlit as st

st.set_page_config(
    page_title="Internal Link AI",
    page_icon="🔗",
    layout="wide"
)

st.title("🔗 Internal Link AI")

st.write(
    "Znajdź naturalne miejsca na linki wewnętrzne "
    "w swoim artykule."
)

st.subheader("Tekst do analizy")

mode = st.radio(
    "Wybierz źródło tekstu:",
    [
        "Mam już artykuł na stronie",
        "Artykuł nie jest jeszcze opublikowany"
    ]
)

article_url = None
article_text = None

if mode == "Mam już artykuł na stronie":

    article_url = st.text_input(
        "URL artykułu",
        placeholder="https://twojastrona.pl/blog/artykul/"
    )

else:

    article_text = st.text_area(
        "Wklej cały tekst artykułu",
        height=300,
        placeholder="Wklej tutaj treść artykułu..."
    )

st.subheader("Sitemap")

sitemap_url = st.text_input(
    "URL sitemap",
    placeholder="https://twojastrona.pl/sitemap.xml"
)

if st.button("🔍 Analizuj linkowanie", type="primary"):

    if mode == "Mam już artykuł na stronie" and not article_url:

        st.error("Podaj URL artykułu.")

    elif mode == "Artykuł nie jest jeszcze opublikowany" and not article_text:

        st.error("Wklej treść artykułu.")

    elif not sitemap_url:

        st.error("Podaj URL sitemap.")

    else:

        st.success("Dane zostały przesłane do analizy.")