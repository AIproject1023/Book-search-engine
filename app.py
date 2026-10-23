
import streamlit as st
import requests
import re

st.set_page_config(page_title="BookBuddy AI", page_icon="📚")
st.title("📚 BookBuddy AI")
st.write("Discover books that match your interests!")

genres = [
    "Any Genre", "Fantasy", "Romance", "Mystery", "Thriller",
    "Horror", "Science Fiction", "Adventure", "Self-Help",
    "Biography", "History", "Psychology", "Science",
    "Technology", "Education", "Crime", "Comedy",
    "Poetry", "Philosophy", "Business", "Health",
    "Sports", "Travel", "Children", "Young Adult",
    "Graphic Novels", "Classics", "Religion"
]

# Well-known popular books; this is a starter list,
# not a live or exhaustive bestseller chart.
popular = [
    "Harry Potter", "The Hobbit", "The Lord of the Rings",
    "The Hunger Games", "The Fault in Our Stars",
    "It Ends with Us", "The Alchemist", "Atomic Habits",
    "The Psychology of Money", "Rich Dad Poor Dad",
    "The Silent Patient", "The Da Vinci Code",
    "A Brief History of Time", "Sapiens",
    "The Book Thief", "Dune", "Twilight",
    "The 7 Habits of Highly Effective People",
    "How to Win Friends and Influence People",
    "To Kill a Mockingbird", "Pride and Prejudice",
    "The Diary of a Young Girl", "Ikigai",
    "The Subtle Art of Not Giving a F*ck"
]

genre = st.selectbox("Choose your favourite genre", genres)
interest = st.text_input(
    "What are you interested in?",
    placeholder="e.g. football, magic, crime, friendship"
)
search = st.text_input(
    "Search for a book or topic",
    placeholder="e.g. books like Harry Potter"
)

if st.button("Find My Books", type="primary"):
    query = " ".join(x for x in [genre if genre != "Any Genre" else "",
                                  interest, search] if x).strip()

    if not query:
        st.warning("Enter a genre, interest, or search topic.")
    else:
        try:
            # Google Books provides live catalogue results.
            url = "https://www.googleapis.com/books/v1/volumes"
            params = {
                "q": query,
                "maxResults": 40,
                "orderBy": "relevance",
                "printType": "books"
            }
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            books = response.json().get("items", [])

            # Search for popular titles separately, too.
            if genre != "Any Genre":
                bestseller_query = "subject:" + genre
            else:
                bestseller_query = interest or search or "popular books"

            extra = requests.get(
                url,
                params={
                    "q": bestseller_query,
                    "maxResults": 40,
                    "orderBy": "relevance",
                    "printType": "books"
                },
                timeout=15
            )
            extra.raise_for_status()
            books += extra.json().get("items", [])

            # Remove duplicate books.
            unique = {}
            for book in books:
                info = book.get("volumeInfo", {})
                title = info.get("title", "")
                if title:
                    unique[title.lower()] = book

            # Score relevance to the user's actual interests.
            words = re.findall(
                r"\w+", (genre + " " + interest + " " + search).lower()
            )
            results = []

            for book in unique.values():
                info = book.get("volumeInfo", {})
                title = info.get("title", "")
                desc = info.get("description", "")
                categories = " ".join(info.get("categories", []))
                author = " ".join(info.get("authors", []))
                text = (title + " " + desc + " " + categories).lower()

                score = sum(3 for w in words if w in title.lower())
                score += sum(1 for w in words if w in text)
                score += sum(
                    2 for w in re.findall(r"\w+", genre.lower())
                    if w in categories.lower()
                )

                # Boost well-known popular titles, but only after
                # relevance is considered.
                is_popular = any(
                    name.lower() in title.lower() for name in popular
                )
                score += 3 if is_popular else 0

                rating = info.get("averageRating", 0)
                score += rating * 0.3

                results.append((score, is_popular, book))

            # Relevance first, then popular titles and ratings.
            results.sort(
                key=lambda x: (x[0], x[1],
                               x[2].get("volumeInfo", {}).get(
                                   "averageRating", 0)),
                reverse=True
            )

            if not results:
                st.info("No books found. Try another keyword.")
            else:
                st.success(f"Found {len(results)} book matches!")
                for score, is_popular, book in results[:20]:
                    info = book.get("volumeInfo", {})
                    title = info.get("title", "Unknown title")
                    authors = ", ".join(info.get("authors", ["Unknown author"]))
                    description = info.get("description", "")
                    image = info.get("imageLinks", {}).get("thumbnail")
                    link = info.get("infoLink", "")
                    rating = info.get("averageRating")
                    categories = ", ".join(info.get("categories", []))

                    with st.container(border=True):
                        if image:
                            st.image(image, width=110)
                        st.subheader(title)
                        st.write("**Author:**", authors)

                        if is_popular:
                            st.caption("⭐ Popular-title match")

                        if rating:
                            st.write(f"Google Books rating: {rating}/5")

                        if categories:
                            st.write("**Categories:**", categories)

                        if description:
                            st.write(description[:450] + (
                                "..." if len(description) > 450 else ""
                            ))

                        if link:
                            st.link_button("View Book", link)

        except requests.RequestException:
            st.error("Could not connect to Google Books. Try again later.")
        except (ValueError, KeyError):
            st.error("Could not read the book results. Please try again.")
