def main(tree_store, context_words, predictive_words):
    first_clause, second_clause = context_words.get("context_window", ["", ""])
    anchor = context_words.get("anchor", "")

    anchor_dict = tree_store.setdefault(anchor, {"score": 0})
    anchor_dict["score"] += 1

    second_clause_dict = anchor_dict.setdefault(second_clause, {"score": 0, first_clause: {"score": 0, "predictions": []}})
    second_clause_dict["score"] += 1

    first_clause_dict = second_clause_dict.setdefault(first_clause, {"score": 0, "predictions": []})
    first_clause_dict["score"] += 1

    predictions = first_clause_dict["predictions"]
    for prediction_dict in predictions:
        if prediction_dict["prediction"] == predictive_words:
            prediction_dict["score"] += 1
            break
    else:  # This else corresponds to the for loop, executed only if the loop completes normally (no break)
        predictions.append({"prediction": predictive_words, "score": 1})

    return tree_store