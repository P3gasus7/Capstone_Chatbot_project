"""
CSC-128 Assignment 6: retrieval
Shawn Canady
"""
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from knowledge import DOCUMENTS

STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "do",
    "does", "did", "you", "your", "i", "we", "for", "of", "to", "in",
    "on", "and", "or", "what", "how", "can", "will", "it", "my", "me",
}

# Set from the scores test_retriever.py prints: the nine real test
# questions matched their correct chunk with scores from 0.122 to
# 0.324, while an unrelated question ("How do I pay my college
# tuition?") scored 0.0 against every chunk. A threshold of 0.10 sits
# safely below every true match and above the unrelated score.
DEFAULT_THRESHOLD = 0.10
DEFAULT_TOP_K = 3


def stem(word):
    """
    Strip common suffixes so that reserve, reserved, and reservation
    collapse to the same token. Not a real Porter stemmer, just enough
    to stop near-identical words from being treated as unrelated.
    """
    word = word.lower()
    for suffix in ("ations", "ation", "ing", "ed", "er", "es", "s", "e"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def analyze(text):
    """Normalize, tokenize, stem, and add bigrams."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [stem(w) for w in text.split() if w not in STOP_WORDS]
    bigrams = ["_".join(pair) for pair in zip(tokens, tokens[1:])]
    return tokens + bigrams


class Retriever:
    def __init__(self, documents=None, threshold=DEFAULT_THRESHOLD):
        self.documents = documents if documents is not None else DOCUMENTS
        self.threshold = threshold
        self.vectorizer = TfidfVectorizer(analyzer=analyze)
        texts = [doc["text"] for doc in self.documents]
        self.doc_vectors = self.vectorizer.fit_transform(texts)

    def search(self, question, top_k=DEFAULT_TOP_K):
        """
        Return a list of (document, score), best first, dropping
        anything below the threshold.

        Returning an empty list is correct and important. It is what
        tells the bot to refuse instead of calling the model with
        nothing useful.
        """
        question_vector = self.vectorizer.transform([question])
        scores = cosine_similarity(question_vector, self.doc_vectors)[0]
        ranked = sorted(
            enumerate(scores), key=lambda pair: pair[1], reverse=True
        )
        hits = []
        for index, score in ranked[:top_k]:
            if score >= self.threshold:
                hits.append((self.documents[index], float(score)))
        return hits

    def build_context(self, hits):
        """Format retrieved chunks for the prompt, with their sources."""
        if not hits:
            return ""
        parts = []
        for doc, score in hits:
            parts.append("[{}] {}".format(doc["source"], doc["text"]))
        return "\n\n".join(parts)
