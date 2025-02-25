import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

def compute_tfidf_top_terms(data, top_n=20, max_features=10000):
    """
    Compute the top TF-IDF terms from a JSON dictionary.
    
    Parameters:
        data (dict): JSON-like dictionary where each key maps to a list.
                     The first element in each list is treated as a long text chunk.
        top_n (int): Number of top terms to return.
        max_features (int): Maximum vocabulary size for the TF-IDF vectorizer.

    Returns:
        list: List of tuples containing (term, TF-IDF sum).
    """

    def preprocess_text(text):
        """Basic text preprocessing: remove non-alphanumeric characters, lowercase."""
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        return text.lower()

    # Extract only the first element of each list (long text chunk)
    documents = []
    for value in data.values():
        documents.append(preprocess_text('\n'.join(value)))

    # Ensure there are documents to process
    if not documents:
        return []

    # Fit TfidfVectorizer
    vectorizer = TfidfVectorizer(
        stop_words='english',
        max_features=max_features,
        max_df=0.95,
        min_df=2
    )
    tfidf_matrix = vectorizer.fit_transform(documents)
    feature_names = vectorizer.get_feature_names_out()

    # Compute the sum of TF-IDF scores for each term
    term_sums = tfidf_matrix.sum(axis=0).A1  # Convert sparse matrix to 1D array
    sorted_indices = np.argsort(term_sums)[::-1]  # Sort descending

    # Return top N terms with their summed TF-IDF scores
    return [(feature_names[idx], term_sums[idx]) for idx in sorted_indices[:top_n]]
