from typing import List, Tuple, Set
from collections import Counter
import numpy as np
import re

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix

def train_committer_model(
    data: List[Tuple[str, str]],
    terms_to_strip: Set[str] = None,
    test_size: float = 0.2,
    random_state: int = 42
):
    """
    Train a simple model to predict the committer from mailing list threads.
    Prints progress, training/test scores, cross-validation results,
    and a classification report & confusion matrix for the test set.
    
    Parameters:
        data (List[Tuple[str, str]]): A list of (mailing_list_text, committer) tuples.
        terms_to_strip (Set[str]): A set of terms to remove from the text before TF-IDF.
        test_size (float): The fraction of data to reserve for testing.
        random_state (int): Random seed for reproducible splits.
    """

    if terms_to_strip is None:
        terms_to_strip = set()

    print("=== Step 1/7: Splitting data into train/test sets (0% complete) ===")
    X_texts = [item[0] for item in data]
    y_committers = [item[1] for item in data]

    # --- Optional: remove classes with <2 samples if you want stratification to work
    # counts = Counter(y_committers)
    # filtered_data = [(x, y) for x, y in zip(X_texts, y_committers) if counts[y] >= 2]
    # X_texts = [fd[0] for fd in filtered_data]
    # y_committers = [fd[1] for fd in filtered_data]

    # Split into train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X_texts, 
        y_committers, 
        test_size=test_size, 
        random_state=random_state,
        stratify=y_committers  # Helps maintain class balance, but requires >=2 samples per class
    )
    print(f"Train size: {len(X_train)} | Test size: {len(X_test)}")
    print("Data split complete. (20% complete)\n")

    # ---------------------------------------------------------
    print("=== Step 2/7: Stripping out custom terms (20% -> 40% complete) ===")
    def remove_terms(text: str, terms: Set[str]) -> str:
        # Simple approach: remove each term if it appears in the text
        for term in terms:
            text = text.replace(term, "")
        return text

    X_train_stripped = [remove_terms(t, terms_to_strip) for t in X_train]
    X_test_stripped = [remove_terms(t, terms_to_strip) for t in X_test]
    print(f"Stripped {len(terms_to_strip)} custom term(s). (40% complete)\n")

    # ---------------------------------------------------------
    print("=== Step 3/7: Running TF-IDF (40% -> 60% complete) ===")
    # Vectorize with TF-IDF
    vectorizer = TfidfVectorizer(
        stop_words='english',
        max_features=100000
    )
    X_train_tfidf = vectorizer.fit_transform(X_train_stripped)
    X_test_tfidf = vectorizer.transform(X_test_stripped)
    print(f"Vocabulary size: {len(vectorizer.get_feature_names_out())}")
    print("TF-IDF complete. (60% complete)\n")

    # ---------------------------------------------------------
    print("=== Step 4/7: Training Logistic Regression model (60% -> 80% complete) ===")
    model = LogisticRegression(
        random_state=random_state, 
        max_iter=1000, 
        n_jobs=-1  # utilize all CPU cores if possible
    )
    model.fit(X_train_tfidf, y_train)

    # Optional: Cross-validation (5-fold) on the training set
    cv_scores = cross_val_score(model, X_train_tfidf, y_train, cv=5, n_jobs=-1)
    print(f"Cross-validation scores (training set): {cv_scores}")
    print(f"Mean CV score: {np.mean(cv_scores):.4f} (80% complete)\n")

    # ---------------------------------------------------------
    print("=== Step 5/7: Evaluating model on training and test sets (80% -> 90% complete) ===")
    train_accuracy = model.score(X_train_tfidf, y_train)
    test_accuracy = model.score(X_test_tfidf, y_test)
    print(f"Training Accuracy: {train_accuracy:.4f}")
    print(f"Test Accuracy:     {test_accuracy:.4f}")

    # ---------------------------------------------------------
    print("=== Step 6/7: Generating precision/recall (classification report) (90% -> 95% complete) ===")
    y_pred_test = model.predict(X_test_tfidf)
    class_report = classification_report(y_test, y_pred_test, zero_division=0)
    print("Classification Report (Test Set):\n", class_report)

    # ---------------------------------------------------------
    print("=== Step 7/7: Generating confusion matrix (95% -> 100% complete) ===")
    conf_mat = confusion_matrix(y_test, y_pred_test)
    print("Confusion Matrix (rows=True label, cols=Predicted label):\n", conf_mat)
    
    # ---------------------------------------------------------
    print("\n=== Done! (100% complete) ===")
    print("Model training & evaluation complete.\n")

    # Optionally return objects if needed
    return model, vectorizer, (train_accuracy, test_accuracy, cv_scores, class_report, conf_mat)


def predict_top_committers(
    model, 
    vectorizer, 
    text: str, 
    top_n: int = 3,
    top_term_count: int = 5
):
    """
    Given a trained model and vectorizer, predict the top N most likely committers
    for a single piece of text. For each predicted class, list only the top
    terms that increased the odds (positive contribution).

    Parameters:
        model: A trained classifier (e.g., LogisticRegression).
        vectorizer: The fitted TfidfVectorizer used during training.
        text (str): The mailing list text to classify.
        top_n (int): Number of top committers to return.
        top_term_count (int): Number of top contributing (positive) terms to list per committer.

    Returns:
        List of tuples:
          [
            (committer, probability, [(term, contribution), ...]),
            ...
          ],
        sorted by descending probability.
    """

    # 1. Transform the text into TF-IDF features
    X_tfidf = vectorizer.transform([text])  # shape = (1, n_features)

    # 2. Get class probabilities
    probas = model.predict_proba(X_tfidf)[0]  # single doc => index [0]

    # 3. Sort probabilities (descending) to get top_n classes
    class_indices_sorted = np.argsort(probas)[::-1]
    top_indices = class_indices_sorted[:top_n]

    # Convert sparse row to dense array for local contribution analysis
    doc_values = X_tfidf.toarray().ravel()
    feature_names = vectorizer.get_feature_names_out()

    results = []
    for class_idx in top_indices:
        class_label = model.classes_[class_idx]
        class_prob = probas[class_idx]

        # 4. Compute contributions of each term = coef * doc's TF-IDF
        class_coefs = model.coef_[class_idx]
        contributions = class_coefs * doc_values

        # 5. Filter out negative or zero contributions (keep only positive)
        #    i.e., terms that truly increase the odds for this class
        positive_contributions = [
            (feat_i, contr_value)
            for feat_i, contr_value in enumerate(contributions)
            if contr_value > 0
        ]

        # 6. Sort descending by the contribution value
        positive_contributions.sort(key=lambda x: x[1], reverse=True)

        # 7. Pick the top 'top_term_count' terms
        top_pos_contribs = positive_contributions[:top_term_count]

        # 8. Build the term list: [(term, contribution), ...]
        top_terms = []
        for feat_i, contr_value in top_pos_contribs:
            term = feature_names[feat_i]
            # top_terms.append((term, float(contr_value)))
            top_terms.append(term)

        results.append((str(class_label), float(class_prob), top_terms))

    return results
