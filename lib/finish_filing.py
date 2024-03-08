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

    # Process each predictive_word and update their scores in the predictions dictionary
    predictions = tree_store[anchor][second_clause][first_clause]["predictions"]
    # Flag to check if a match is found
    match_found = False

    # Iterate through each dictionary in predictions
    for prediction_dict in predictions:
        if prediction_dict["prediction"] == predictive_words:
            # If match is found, increment the score and update the flag
            prediction_dict["score"] += 1
            match_found = True
            break

    # If no match is found, add a new dictionary to the predictions array
    if not match_found:
        predictions.append({"prediction": predictive_words, "score": 1})

    return tree_store