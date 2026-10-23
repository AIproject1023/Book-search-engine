
import streamlit as st
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(page_title="BookBuddy AI", page_icon="📚")
st.title("📚 BookBuddy AI")
st.write("Find books that match your interests!")

genre = st.selectbox("Choose genre", [
    "Any Genre", "Fantasy", "Romance", "Mystery", "Thriller",
    "Horror", "Science Fiction", "Adventure", "Self-Help",
    "Biography", "History", "Psychology", "Science",
    "Technology", "Education", "Crime", "Poetry", "Business",
    "Sports", "Children", "Young Adult", "Classics"
])
interest = st.text_input("Your interests", placeholder="magic, football, motivation")
search = st.text_input("Search books", placeholder="books about space")

popular = [
    "Harry Potter", "The Hobbit", "The Hunger Games",
    "Atomic Habits", "The Alchemist", "Sapiens",
    "The Silent Patient", "Dune", "Ikigai",
    "The Psychology of Money", "The Da Vinci Code",
    "Pride and Prejudice", "The Book Thief"
]

if st.button("Recommend Books"):
    query = " ".join(x for x in [
        genre if genre != "Any Genre" else "", interest, search
    ] if x).strip()

    if not query:
        st.warning("Enter a genre, interest, or search.")
    else:
        try:
            response = requests.get(
                "https://www.googleapis.com/books/v1/volumes",
                params={"q": query, "maxResults": 40,
                        "orderBy": "relevance", "printType": "books"},
                timeout=15
            )
            response.raise_for_status()
            books = response.json().get("items", [])

            # Remove duplicates and books without titles
            unique = {}
            for b in books:
                info = b.get("volumeInfo", {})
                title = info.get("title", "")
                if title:
                    unique[title.lower()] = b
            books = list(unique.values())

            if not books:
                st.info("No books found. Try different keywords.")
            else:
                texts = []
                for b in books:
                    i = b.get("volumeInfo", {})
                    texts.append(" ".join([
                        i.get("title", ""),
                        i.get("description", ""),
                        " ".join(i.get("categories", []))
                    ]))

                # Fit the AI text model to retrieved books
                model = TfidfVectorizer(stop_words="english")
                vectors = model.fit_transform(texts)
                scores = cosine_similarity(
                    model.transform([query]), vectors
                ).flatten()

                ranked = []
                for n, b in enumerate(books):
                    i = b.get("volumeInfo", {})
                    title = i.get("title", "")
                    bestseller_match = any(
                        p.lower() in title.lower() for p in popular
                    )
                    score = scores[n] + (0.05 if bestseller_match else 0)
                    ranked.append((score, scores[n], b, bestseller_match))

                ranked.sort(key=lambda x: (x[0], x[1]), reverse=True)
                st.success("Your recommended books:")

                for score, relevance, b, popular_match in ranked[:15]:
                    i = b.get("volumeInfo", {})
                    st.subheader(i.get("title", "Unknown title"))
                    st.write("**Author:** " + ", ".join(
                        i.get("authors", ["Unknown"])
                    ))
                    if popular_match:
                        st.caption("⭐ Popular-title match (not a live bestseller ranking)")
                    if i.get("imageLinks", {}).get("thumbnail"):
                        st.image(i["imageLinks"]["thumbnail"], width=100)
                    st.write(i.get("description", "No description available.")[:350])
                    st.write("**Match score:** " + str(round(relevance * 100)) + "%")
                    if i.get("infoLink"):
                        st.link_button("View Book", i["infoLink"])
                    st.divider()

        except requests.RequestException:
            st.error("Google Books is unavailable. Please try again.")
        except ValueError:
            st.error("Could not read the book data. Please try again.")
        except Exception as e:
            st.error("Something went wrong: " + str(e))
