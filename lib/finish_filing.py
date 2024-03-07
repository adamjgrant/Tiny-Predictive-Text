def tokenize_word(token_dict, word):
    """Assigns a unique integer token to a word if it's not already tokenized."""
    if word not in token_dict:
        # Assign the next available integer as the token
        token_dict[word] = len(token_dict) + 1
    return token_dict[word]

def main(tree_store, token_dict, context_words, predictive_words):
    first_clause, second_clause = context_words.get("context_window", ["", ""])
    anchor = context_words.get("anchor", "")

    # Tokenize the anchor, first_clause, and second_clause
    anchor_token = tokenize_word(token_dict, anchor)
    first_clause_token = tokenize_word(token_dict, first_clause)
    second_clause_token = tokenize_word(token_dict, second_clause)

    # Initialize or update the anchor in the tree using its token
    if anchor_token not in tree_store:
        tree_store[anchor_token] = {"score": 0}

    tree_store[anchor_token]["score"] += 1

    # Initialize or update the second_clause within the anchor using its token
    if second_clause_token not in tree_store[anchor_token]:
        tree_store[anchor_token][second_clause_token] = {"score": 0, first_clause_token: {"score": 0, "predictions": {}}}

    tree_store[anchor_token][second_clause_token]["score"] += 1

    # Initialize or update the first_clause within the second_clause using its token
    if first_clause_token not in tree_store[anchor_token][second_clause_token]:
        tree_store[anchor_token][second_clause_token][first_clause_token] = {"score": 0, "predictions": {}}

    tree_store[anchor_token][second_clause_token][first_clause_token]["score"] += 1

    # Process each predictive_word, tokenize it, and update their scores in the predictions dictionary
    predictions_dict = tree_store[anchor_token][second_clause_token][first_clause_token]["predictions"]
    for predictive_word in predictive_words:
        pw_token = tokenize_word(token_dict, predictive_word)
        if pw_token not in predictions_dict:
            predictions_dict[pw_token] = 1  # Initialize with a score of 1
        else:
            predictions_dict[pw_token] += 1  # Increment the score

    return [tree_store, token_dict]
