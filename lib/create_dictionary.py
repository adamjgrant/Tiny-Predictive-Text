import json
import msgpack
import copy
import asyncio

SUBBRANCH_PRUNE_SIZE = 4
MAX_PREDICTIONS = 3
next_token = 0
token_dict = {}
word_dict = {}

def regsiter_string_with_token_dictionary(string):
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
              # Skip special keys "_" and "-"
              if key in ["-"]:
                continue

              if key == "_":
                _keys = list(node["_"].keys())
                for _key in _keys:
                  _token = regsiter_string_with_token_dictionary(_key)
                  node["_"][_token] = node["_"].pop(_key)
                continue

              # Register token
              token = regsiter_string_with_token_dictionary(key)

              # Swap out the keyname for the token.
              node[token] = node.pop(key, None)

              # Recursively process the value
              node[token] = tokenize_tree(node[token])

        return node

    return tokenize_tree(tree)
  
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
        pruned_tree = tree
        keys_to_delete = list(tree.keys())[limit:len(tree.keys())]
        for key in keys_to_delete:
          pruned_tree.pop(key)
        return pruned_tree

    top_sorted_tree = sort_keys_by_score(tree_store)
    top_pruned_tree = prune_top_level_entries_by_limit(top_sorted_tree, target_dict_size)

    def prune_and_sort_lower_branches(subtree, limit):
        if isinstance(subtree, dict):
            # Special handling to preserve the "-" and "_" keys correctly
            score = subtree.get('-', False)  # Preserve the existing score, if any
            predictions = subtree.get('_', False)  # Preserve predictions, if any
            
            # Filter out the special keys for sorting and pruning operations
            filtered_subtree = {k: v for k, v in subtree.items() if k not in ['-', '_']}
            
            top_sorted_subtree = sort_keys_by_score(filtered_subtree)
            pruned_subtree = prune_top_level_entries_by_limit(top_sorted_subtree, limit)
            
            # Re-insert the preserved score and predictions into the pruned subtree
            if score:
                pruned_subtree['-'] = score
            
            if predictions:  # Check if there's something to re-insert
                # Sort the dictionary by value in descending order and slice to keep only MAX_PREDICTIONS items
                sorted_items = sorted(predictions.items(), key=lambda x: x[1], reverse=True)[:MAX_PREDICTIONS]
                pruned_subtree['_'] = dict(sorted_items)

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
    # Then, create a token dictionary and update the tree in-place
    print("Tokenizing")
    tokened_pruned_tree = create_token_dict(pruned_tree)
    
    save_to_dict_files(tokened_pruned_tree, token_dict)
    return