import json
import msgpack
import copy
import asyncio
import logging

# Setup basic configuration for logging
logging.basicConfig(level=logging.DEBUG)

SUBBRANCH_PRUNE_SIZE = 4
MAX_PREDICTIONS = 3
next_token = 0 # Will be incremented by 1 on first usage.
token_dict = {0: "predictions"}
word_dict = {"predictions": 0}

def register_string_with_token_dictionary(string):
  global next_token
  global token_dict
  global word_dict

  if string not in word_dict:
    next_token += 1
    token_dict[next_token] = string
    word_dict[string] = next_token

  used_token = word_dict[string]

  return used_token

def create_token_dict(tree):
    def tokenize_tree(node):
        global token_dict
        if isinstance(node, dict) and len(node.items()):
            keys = list(node.keys())
            for key in keys:
              if key == "predictions":
                prediction_super_array = list(node["predictions"])
                for index, prediction_array in enumerate(prediction_super_array):
                    tokenized_prediction_array = list(map(lambda word: register_string_with_token_dictionary(word), prediction_array)) 
                    node[key][index] = tokenized_prediction_array

              # Register token
              token = register_string_with_token_dictionary(key)

              # Swap out the keyname for the token.
              node[token] = node.pop(key, None)

              # Recursively process the value
              node[token] = tokenize_tree(node[token])

        return node

    return tokenize_tree(tree)
  
def create_dictionary(tree_store, target_dict_size):
    def sort_keys_by_score(tree):
        # Sorts the tree's top-level keys based on their child score "score", highest first
        # Keeps the "score" key intact
        sorted_items = sorted(
            [(k, v) for k, v in tree.items() if k != "score" and isinstance(v, dict)],
            key=lambda item: item[1]["score"] if "score" in item[1] else 0, reverse=True
        )
        sorted_tree = {"score": tree.get("score", 0)} if "score" in tree else {}  # Preserve "score" score if it exists
        sorted_tree.update(dict(sorted_items))
        return sorted_tree

    def prune_top_level_entries_by_limit(tree, limit):
        pruned_tree = tree
        keys_to_delete = list(tree.keys())[limit:len(tree.keys())]
        for key in keys_to_delete:
          pruned_tree.pop(key)
        return pruned_tree

    top_sorted_tree = sort_keys_by_score(tree_store)
    top_pruned_tree = prune_top_level_entries_by_limit(top_sorted_tree, target_dict_size)

    def prune_and_sort_lower_branches(subtree, limit):
        if isinstance(subtree, dict):
            # Special handling to preserve the "score" and "predictions" keys correctly
            score = subtree.get("score", False)  # Preserve the existing score, if any
            predictions = subtree.get("predictions", False)  # Preserve predictions, if any
            
            # Filter out the special keys for sorting and pruning operations
            filtered_subtree = {k: v for k, v in subtree.items() if k not in ["score", "predictions"]}
            
            top_sorted_subtree = sort_keys_by_score(filtered_subtree)
            pruned_subtree = prune_top_level_entries_by_limit(top_sorted_subtree, limit)
            
            # Re-insert the preserved score and predictions into the pruned subtree
            if score:
                pruned_subtree["score"] = score
            
            if predictions:  # Check if there's something to re-insert
              # Sort the list of dictionaries by the 'score' key in descending order and slice to keep only MAX_PREDICTIONS items
              sorted_predictions = sorted(predictions, key=lambda x: x['score'], reverse=True)[:MAX_PREDICTIONS]
              pruned_subtree["predictions"] = sorted_predictions

            # Recursively process each child, skipping special keys
            for k, v in list(pruned_subtree.items()):
                if k not in ["score", "predictions"] and isinstance(v, dict):
                    pruned_subtree[k] = prune_and_sort_lower_branches(v, SUBBRANCH_PRUNE_SIZE)
                    
            return pruned_subtree
        else:
              return subtree

    for k in list(top_pruned_tree.keys()):
        if k != "score":
            subtree = top_pruned_tree[k]
            top_pruned_tree[k] = prune_and_sort_lower_branches(subtree, SUBBRANCH_PRUNE_SIZE)

    return top_pruned_tree

def remove_scores_and_flatten_predictions(tree):
    if isinstance(tree, dict):
        # If the tree is a dictionary, iterate over its keys
        keys_list = list(tree.keys())  # List of keys to iterate over, avoiding 'RuntimeError: dictionary changed size during iteration'
        for key in keys_list:
            if key == "score":
                # Remove the 'score' key
                tree.pop(key)
            elif key == "predictions" and isinstance(tree[key], list):
                # Flatten the 'predictions' array
                tree[key] = [pred["prediction"] for pred in tree[key] if "prediction" in pred]
            else:
                # Recurse for nested dictionaries
                remove_scores_and_flatten_predictions(tree[key])
    return tree

def save_to_dict_files(pruned_tree, token_dict):
    print("Saving dictionaries to files.")
    with open('dictionary.msgpack', 'wb') as dict_file:  # Note the 'wb' mode for binary writing
      msgpack.dump(pruned_tree, dict_file)

    with open('tokens.msgpack', 'wb') as dict_file:  # Note the 'wb' mode for binary writing
      msgpack.dump(token_dict, dict_file)
  
async def create_dictionary_and_tokenize(tree_store, target_dict_size):
    global token_dict
    print("Creating dictionary and tokenizing")

    # First, prune and sort the dictionary based on scores
    print("Pruning")
    pruned_tree = create_dictionary(tree_store, target_dict_size)

    # Remove score values and other complications we don't need in the final dict.
    print("Simplifying")
    # Allow the running program to keep working on the unsimplified and untokenized tree.
    simplified_pruned_tree = remove_scores_and_flatten_predictions(copy.deepcopy(pruned_tree))

    # Then, create a token dictionary and update the tree in-place
    print("Tokenizing")
    tokened_pruned_tree = create_token_dict(simplified_pruned_tree)
    
    # Save to actual files.
    save_to_dict_files(tokened_pruned_tree, token_dict)
    return