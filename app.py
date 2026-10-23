
import streamlit as st
import pandas as pd
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(page_title="BookBuddy AI", page_icon="📚")
st.title("📚 BookBuddy AI")
st.write("AI-powered personalized book recommendations")

GENRES = [
    "Any Genre", "Fantasy", "Romance", "Mystery", "Thriller",
    "Horror", "Science Fiction", "Adventure", "Self-Help",
    "Biography", "History", "Psychology", "Science", "Technology",
    "Education", "Crime", "Poetry", "Business", "Sports",
    "Children", "Young Adult", "Classics", "Medicine", "Philosophy"
]

genre = st.selectbox("Select genre", GENRES)
interest = st.text_input("Your interests", placeholder="magic, football, science")
search = st.text_input("Search books", placeholder="books about space")

if st.button("Recommend Books"):
    query = " ".join(
        x for x in [
            genre if genre != "Any Genre" else "",
            interest, search
        ] if x
    ).strip()

    if not query:
        st.warning("Enter a genre, interest, or search topic.")
        st.stop()

    # Load your CSV dataset
    try:
        df = pd.read_csv("book_recommendation_dataset.csv").fillna("")
        local_books = df.to_dict("records")
    except (FileNotFoundError, pd.errors.ParserError):
        st.error("Upload book_recommendation_dataset.csv to GitHub.")
        st.stop()

    books = []

    # Add books from your CSV
    for b in local_books:
        books.append({
            "title": str(b.get("title", "")),
            "authors": str(b.get("authors", "Unknown")),
            "categories": str(b.get("categories", "")),
            "description": str(b.get("interests", "")),
            "link": "", "image": "",
            "popular": str(b.get("popularity_note", ""))
        })

    # Add live books from Google Books
    api_ok = False
    try:
        r = requests.get(
            "https://www.googleapis.com/books/v1/volumes",
            params={"q": query, "maxResults": 40,
                    "orderBy": "relevance", "printType": "books"},
            timeout=15
        )
        r.raise_for_status()
        api_ok = True

        for item in r.json().get("items", []):
            b = item.get("volumeInfo", {})
            books.append({
                "title": b.get("title", ""),
                "authors": ", ".join(b.get("authors", ["Unknown"])),
                "categories": ", ".join(b.get("categories", [])),
                "description": b.get("description", ""),
                "link": b.get("infoLink", ""),
                "image": b.get("imageLinks", {}).get("thumbnail", ""),
                "popular": ""
            })
    except (requests.RequestException, ValueError):
        st.warning("Google Books is unavailable. Showing CSV books instead.")

    # Remove duplicate titles
    unique = {}
    for b in books:
        if b["title"].strip():
            key = b["title"].strip().lower()
            if key not in unique or (b["link"] and not unique[key]["link"]):
                unique[key] = b

    books = list(unique.values())

    if not books:
        st.error("No books available.")
        st.stop()

    # AI: learn text features and match user preferences
    documents = [
        " ".join([
            b["title"], b["authors"], b["categories"], b["description"]
        ])
        for b in books
    ]

    model = TfidfVectorizer(stop_words="english")
    vectors = model.fit_transform(documents)
    scores = cosine_similarity(
        model.transform([query]), vectors
    ).flatten()

    ranked = []
    for n, b in enumerate(books):
        # Small boost for known popular titles in the starter CSV
        popular = bool(b["popular"])
        score = scores[n] + (0.03 if popular else 0)
        ranked.append((score, scores[n], b, popular))

    ranked.sort(key=lambda x: (x[0], x[1]), reverse=True)

    st.success(f"Found {len(ranked)} recommendations!")
    if not api_ok:
        st.caption("Results are from your local CSV dataset.")

    for score, relevance, b, popular in ranked[:20]:
        with st.container(border=True):
            st.subheader(b["title"])
            st.write("**Author:**", b["authors"])
            if b["categories"]:
                st.write("**Genre:**", b["categories"])
            if popular:
                st.caption("⭐ Popular-title entry in your CSV")
            if b["image"]:
                st.image(b["image"], width=100)
            if b["description"]:
                st.write(b["description"][:350])
            st.write(f"**Text relevance:** {relevance * 100:.1f}%")
            if b["link"]:
                st.link_button("View Book", b["link"])
