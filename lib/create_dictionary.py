import json

SUBBRANCH_PRUNE_SIZE = 4

def create_token_dict(tree):
    return tree
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
        # Sorts the tree's top-level keys based on their child score "-", highest first
        # Keeps the "-" key intact
        sorted_items = sorted(
            [(k, v) for k, v in tree.items() if k != '-' and isinstance(v, dict)],
            key=lambda item: item[1]['-'] if '-' in item[1] else 0, reverse=True
        )
        sorted_tree = {'-': tree.get('-', 0)} if '-' in tree else {}  # Preserve "-" score if it exists
        sorted_tree.update(dict(sorted_items))
        return sorted_tree

    def prune_top_level_entries_by_limit(tree, limit):
        # Prunes the tree to keep only the first `limit` number of top-level entries, excluding the "-" key
        pruned_tree = {'-': tree['-']} if '-' in tree else {}  # Preserve "-" score
        pruned_tree.update(dict(list(tree.items())[1:limit+1]))  # +1 to account for "-" key not being pruned
        return pruned_tree

    top_sorted_tree = sort_keys_by_score(tree_store)
    top_pruned_tree = prune_top_level_entries_by_limit(top_sorted_tree, target_dict_size)

    def prune_and_sort_lower_branches(subtree, limit):
        if isinstance(subtree, dict):
            # Special handling to preserve the "-" and "_" keys correctly
            score = subtree.get('-', 0)  # Preserve the existing score, if any
            predictions = subtree.get('_', {})  # Preserve predictions, if any
            
            # Filter out the special keys for sorting and pruning operations
            filtered_subtree = {k: v for k, v in subtree.items() if k not in ['-', '_']}
            
            top_sorted_subtree = sort_keys_by_score(filtered_subtree)
            pruned_subtree = prune_top_level_entries_by_limit(top_sorted_subtree, limit)
            
            # Re-insert the preserved score and predictions into the pruned subtree
            if score or predictions:  # Check if there's something to re-insert
                pruned_subtree['_'] = predictions
                pruned_subtree['-'] = score

            # Recursively process each child, skipping special keys
            for k, v in list(pruned_subtree.items()):
                if k not in ['-', '_'] and isinstance(v, dict):
                    pruned_subtree[k] = prune_and_sort_lower_branches(v, SUBBRANCH_PRUNE_SIZE)
                    
            return pruned_subtree
        else:
              return subtree

    for k in list(top_pruned_tree.keys()):
        if k != '-':
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