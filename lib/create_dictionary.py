import json

SUBBRANCH_PRUNE_SIZE = 4

def create_token_dict(tree):
    token_dict = {}
    current_token = 0  # Start token numbering from 0 or 1 based on your preference

    def assign_tokens(node):
        nonlocal current_token
        if isinstance(node, dict):
            for key in list(node.keys()):  # Use list(node.keys()) to avoid RuntimeError
                value = node[key]
                if key != "-" and not isinstance(value, int):
                    # Assign a token if the word doesn't have one yet
                    if key not in token_dict:
                        token_dict[key] = current_token
                        current_token += 1
                    # Replace the key with its token in the node
                    tokenized_key = token_dict[key]
                    node[tokenized_key] = node.pop(key)
                    assign_tokens(node[tokenized_key])  # Recursively assign tokens
                else:
                    assign_tokens(value)  # Recursively assign tokens for nested dictionaries or values
        
    assign_tokens(tree)
    return token_dict
  
def create_dictionary(tree_store, target_dict_size):
    def sort_keys_by_score(tree):
        # Sorts the tree's top-level keys based on their child score ("-") value, highest first
        return dict(sorted(tree.items(), key=lambda item: item[1]['-'] if isinstance(item[1], dict) and '-' in item[1] else 0, reverse=True))

    def prune_top_level_entries_by_limit(tree, limit):
        # Keeps only the first `limit` number of top-level entries
        return dict(list(tree.items())[:limit])

    top_sorted_tree = sort_keys_by_score(tree_store)
    top_pruned_tree = prune_top_level_entries_by_limit(top_sorted_tree, target_dict_size)

    def prune_and_sort_lower_branches(subtree, limit):
        if isinstance(subtree, dict):
            top_sorted_subtree = sort_keys_by_score(subtree)
            pruned_subtree = prune_top_level_entries_by_limit(top_sorted_subtree, limit)
            for k, v in pruned_subtree.items():
                # Recursively apply pruning and sorting to lower branches if v is a dict
                pruned_subtree[k] = prune_and_sort_lower_branches(v, SUBBRANCH_PRUNE_SIZE)
            return pruned_subtree
        else:
            return subtree

    for k in list(top_pruned_tree.keys()):
        subtree = top_pruned_tree[k]
        top_pruned_tree[k] = prune_and_sort_lower_branches(subtree, SUBBRANCH_PRUNE_SIZE)

    return top_pruned_tree

def save_to_json_files(pruned_tree, token_dict):
    # Save the tokenized tree to dictionary.json
    with open('dictionary.json', 'w') as dict_file:
        json.dump(pruned_tree, dict_file)
    
    # Save the token dictionary to tokens.json
    with open('tokens.json', 'w') as token_file:
        json.dump(token_dict, token_file)
  
def create_dictionary_and_tokenize(tree_store, target_dict_size):
    # First, prune and sort the dictionary based on scores
    pruned_tree = create_dictionary(tree_store, target_dict_size)
    # Then, create a token dictionary and update the tree in-place
    token_dict = create_token_dict(pruned_tree)
    
    save_to_json_files(pruned_tree, token_dict)