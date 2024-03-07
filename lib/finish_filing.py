def main(tree_store, context_words, predictive_words):
    first_clause, second_clause = context_words.get("context_window", ["", ""])
    anchor = context_words.get("anchor", "")

    # Initialize or update the anchor in the tree
    if anchor not in tree_store:
        tree_store[anchor] = {"score": 0}

    tree_store[anchor]["score"] += 1

    # Initialize or update the second_clause within the anchor
    if second_clause not in tree_store[anchor]:
        tree_store[anchor][second_clause] = {"score": 0, first_clause: {"score": 0, "predictions": []}}

    tree_store[anchor][second_clause]["score"] += 1

    # Initialize or update the first_clause within the second_clause
    if first_clause not in tree_store[anchor][second_clause]:
        tree_store[anchor][second_clause][first_clause] = {"score": 0, "predictions": []}

    tree_store[anchor][second_clause][first_clause]["score"] += 1

    # Add predictive_words to the predictions array if not already present
    predictions = tree_store[anchor][second_clause][first_clause]["predictions"]
    if predictive_words not in predictions:
        predictions.append(predictive_words)

    return tree_store