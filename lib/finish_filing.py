def main(tree_store, context_words, predictive_words):
    first_clause, second_clause = context_words.get("context_window", ["", ""])
    anchor = context_words.get("anchor", "")

    # Initialize or update the anchor in the tree
    if anchor not in tree_store:
        tree_store[anchor] = {"-": 0}

    tree_store[anchor]["-"] += 1

    # Initialize or update the second_clause within the anchor
    if second_clause not in tree_store[anchor]:
        tree_store[anchor][second_clause] = {"-": 0, first_clause: {"-": 0, "_": {}}}

    tree_store[anchor][second_clause]["-"] += 1

    # Initialize or update the first_clause within the second_clause
    if first_clause not in tree_store[anchor][second_clause]:
        tree_store[anchor][second_clause][first_clause] = {"-": 0, "_": {}}

    tree_store[anchor][second_clause][first_clause]["-"] += 1

    # Process each predictive_word and update their scores in the predictions dictionary
    predictions_dict = tree_store[anchor][second_clause][first_clause]["_"]
    for predictive_word in predictive_words:
        if predictive_word not in predictions_dict:
            predictions_dict[predictive_word] = 1  # Initialize with a score of 1
        else:
            predictions_dict[predictive_word] += 1  # Increment the score

    return tree_store