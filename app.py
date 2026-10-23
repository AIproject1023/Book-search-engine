
import streamlit as st
import pandas as pd
import re
from collections import Counter
from math import log

st.title("📚 BookBuddy AI")
st.write("AI Book Recommendation System using NLP")

genre = st.selectbox("Choose Genre", [
    "Any Genre", "Fantasy", "Romance", "Mystery", "Thriller",
    "Horror", "Science Fiction", "Adventure", "Self-Help",
    "Biography", "History", "Psychology", "Science",
    "Technology", "Education", "Crime", "Poetry",
    "Business", "Sports", "Children", "Classics"
])
interest = st.text_input("Your interests", placeholder="magic, friendship")
search = st.text_input("Search books", placeholder="books about space")

def clean(text):
    return re.findall(r"[a-z]+", str(text).lower())

if st.button("Recommend Books"):
    try:
        df = pd.read_csv("book_recommendation_dataset.csv").fillna("")
        query = clean(interest + " " + search)
        if genre != "Any Genre":
            query += clean(genre)

        if not query:
            st.warning("Enter your interests or search keywords.")
            st.stop()

        documents = []
        for _, b in df.iterrows():
            text = " ".join([
                str(b["title"]), str(b["categories"]),
                str(b["interests"]), str(b["authors"])
            ])
            documents.append(set(clean(text)))

        # Simple TF-IDF-style word weighting
        total = len(documents)
        idf = {}
        for word in set(query):
            count = sum(word in doc for doc in documents)
            idf[word] = log((total + 1) / (count + 1)) + 1

        results = []
        for i, doc in enumerate(documents):
            score = sum(idf.get(w, 1) for w in query if w in doc)

            if genre != "Any Genre":
                if genre.lower() in str(df.iloc[i]["categories"]).lower():
                    score += 3

            if score > 0:
                results.append((score, i))

        results.sort(reverse=True)

        if not results:
            st.info("No matches found. Try different keywords.")
        else:
            st.success("Recommended books")
            for score, i in results[:20]:
                b = df.iloc[i]
                st.subheader(b["title"])
                st.write("**Author:**", b["authors"])
                st.write("**Genre:**", b["categories"])
                st.write("**Interests:**", b["interests"])
                st.write("**AI match score:**", round(score, 2))
                st.divider()

    except FileNotFoundError:
        st.error("Upload book_recommendation_dataset.csv to GitHub.")
    except Exception as e:
        st.error("Error: " + str(e))


