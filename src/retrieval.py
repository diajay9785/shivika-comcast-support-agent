"""
Grounding retrieval for drafted replies.

Builds a corpus of (customer message -> ComcastCares reply) pairs from the
cleaned historical thread data, then retrieves the n most similar past
customer messages to a new incoming message via TF-IDF cosine similarity.
The retrieved replies are what draft.py uses to match ComcastCares' real
historical tone (see identity/entity.md).
"""

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_corpus_df = None
_vectorizer = None
_corpus_matrix = None


def build_corpus(threads_csv_path, exclude_roots=None):
    """
    Call this once at startup. Builds customer->reply pairs from the full
    cleaned thread pool (not the small working sample -- more grounding
    examples to draw from).

    exclude_roots: iterable of thread 'root' ids to leave out of the corpus.
    Always pass the golden-set thread roots here during evaluation, so the
    system can't retrieve its own answer for a golden-set example
    (see decision_log.md #13).
    """
    global _corpus_df, _vectorizer, _corpus_matrix

    df = pd.read_csv(threads_csv_path)
    if exclude_roots:
        df = df[~df["root"].isin(exclude_roots)]

    df = df.sort_values("created_at")

    pairs = []
    for root, group in df.groupby("root"):
        group = group.sort_values("created_at")
        customer_msgs = group[group["inbound"] == True]
        comcast_msgs = group[group["author_id"] == "comcastcares"]
        if len(customer_msgs) == 0 or len(comcast_msgs) == 0:
            continue
        # first customer message, first comcastcares reply -- good enough
        # signal for a "what did they say back" grounding example
        pairs.append({
            "text": customer_msgs.iloc[0]["text"],
            "response": comcast_msgs.iloc[0]["text"],
        })

    _corpus_df = pd.DataFrame(pairs)
    _vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    _corpus_matrix = _vectorizer.fit_transform(_corpus_df["text"])

    return len(_corpus_df)


def retrieve_examples(query_text, n=3):
    """
    Returns up to n most similar historical (text, response) pairs to
    query_text, as a list of dicts with 'text' and 'response'.
    """
    if _corpus_df is None:
        raise RuntimeError("Call build_corpus() before retrieve_examples().")

    query_vec = _vectorizer.transform([query_text])
    sims = cosine_similarity(query_vec, _corpus_matrix).flatten()
    top_idx = sims.argsort()[::-1][:n]

    return _corpus_df.iloc[top_idx].to_dict("records")