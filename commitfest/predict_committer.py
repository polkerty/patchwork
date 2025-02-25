from typing import List, Tuple, Set
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

def train_committer_model(
    data: List[Tuple[str, str]],
    terms_to_strip: Set[str] = None,
    test_size: float = 0.2,
    random_state: int = 42
):
    """
    Train a simple model to predict the committer from mailing list threads.
    
    Parameters:
        data (List[Tuple[str, str]]): A list of (mailing_list_text, committer) tuples.
        terms_to_strip (Set[str]): A set of terms to remove from the text before TF-IDF.
        test_size (float): The fraction of data to reserve for testing.
        random_state (int): Random seed for reproducible splits.
    
    Returns:
        None. Prints out progress, training/test scores, and cross-validation results.
    """

    if terms_to_strip is None:
        terms_to_strip = set()

    print("=== Step 1/6: Splitting data into train/test sets (0% complete) ===")
    X_texts = [item[0] for item in data]
    y_committers = [item[1] for item in data]

    # Split into train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X_texts, y_committers, 
        test_size=test_size, 
        random_state=random_state,
        stratify=y_committers  # helps maintain class balance
    )
    print(f"Train size: {len(X_train)} | Test size: {len(X_test)}")
    print("Data split complete. (20% complete)\n")

    # ---------------------------------------------------------
    print("=== Step 2/6: Stripping out custom terms (20% -> 40% complete) ===")
    def remove_terms(text: str, terms: Set[str]) -> str:
        # Simple approach: remove each term if it appears as a standalone word
        # You could also do more advanced text cleaning here.
        for term in terms:
            # Replace with blank if found as a full word
            text = text.replace(term, "")
        return text

    X_train_stripped = [remove_terms(t, terms_to_strip) for t in X_train]
    X_test_stripped = [remove_terms(t, terms_to_strip) for t in X_test]
    print(f"Stripped {len(terms_to_strip)} custom term(s). (40% complete)\n")

    # ---------------------------------------------------------
    print("=== Step 3/6: Running TF-IDF (40% -> 60% complete) ===")
    # Use all cores available: n_jobs=-1
    vectorizer = TfidfVectorizer(stop_words='english', max_features=100000)
    X_train_tfidf = vectorizer.fit_transform(X_train_stripped)
    X_test_tfidf = vectorizer.transform(X_test_stripped)
    print(f"Vocabulary size: {len(vectorizer.get_feature_names_out())}")
    print("TF-IDF complete. (60% complete)\n")

    # ---------------------------------------------------------
    print("=== Step 4/6: Training Logistic Regression model (60% -> 80% complete) ===")
    # Use multiple cores with n_jobs=-1
    model = LogisticRegression(
        random_state=random_state, 
        max_iter=1000, 
        n_jobs=-1  # utilize all CPU cores
    )
    model.fit(X_train_tfidf, y_train)

    # Optional: Cross-validation on the training set (e.g., 5-fold)
    cv_scores = cross_val_score(model, X_train_tfidf, y_train, cv=5, n_jobs=-1)
    print(f"Cross-validation scores (training set): {cv_scores}")
    print(f"Mean CV score: {np.mean(cv_scores):.4f} (80% complete)\n")

    # ---------------------------------------------------------
    print("=== Step 5/6: Evaluating model on training and test sets (80% -> 100% complete) ===")
    train_accuracy = model.score(X_train_tfidf, y_train)
    test_accuracy = model.score(X_test_tfidf, y_test)
    print(f"Training Accuracy: {train_accuracy:.4f}")
    print(f"Test Accuracy:     {test_accuracy:.4f}")

    # ---------------------------------------------------------
    print("\n=== Done! (100% complete) ===")
    print("Model training & evaluation complete.\n")

    # You could return the model, vectorizer, or scores as needed:
    # return model, vectorizer, (train_accuracy, test_accuracy, cv_scores)
