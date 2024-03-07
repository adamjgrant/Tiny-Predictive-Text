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

def create_dictionary(tree_store, target_dict_size, subbranch_prune_size=4):
    def sort_and_prune(current_dict, target_size, is_top_level=True):
        target_size = int(target_size)
        # Create a new dictionary to hold pruned items
        pruned_items = {}

        # First, sort the current level items by their score in descending order, excluding '-' key itself
        sorted_items = sorted(
            [(k, v) for k, v in current_dict.items() if isinstance(v, dict) and '-' in v],
            key=lambda item: item[1]['-'],
            reverse=True
        )

        # Prune to keep only the top target_size items at the current level
        pruned_keys = [k for k, _ in sorted_items[:target_size]]
        
        # Now, go through the pruned keys to recursively sort and prune children or predictions
        for key in pruned_keys:
            item = current_dict[key]
            pruned_items[key] = item  # Keep the entire item, including the '-'

            # If this item has any nested structure that needs sorting and pruning, do it recursively
            if isinstance(item, dict):
                for subkey, subvalue in item.items():
                    if isinstance(subvalue, dict):
                        # Sort and prune recursively
                        # Apply subbranch prune size for non-top-level items
                        next_target_size = subbranch_prune_size if not is_top_level else target_size
                        pruned_items[key][subkey] = sort_and_prune(subvalue, next_target_size, False)
        
        return pruned_items

    # Start the recursive sorting and pruning from the root with the top level flag set to True
    pruned_tree = sort_and_prune(tree_store, target_dict_size, True)

    return pruned_tree
  
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