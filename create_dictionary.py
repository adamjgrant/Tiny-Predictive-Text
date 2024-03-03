import os
import json

# Across all dictionaries, how many entry word sets total should we regularly prune the 
# dictionary back to contain?
TARGET_DICTIONARY_COUNT = 15000 

# Of the total TARGET_DICTIONARY_COUNT, what stake in that count should each dictionary get?
THREE_WORD_STAKE_PERCENT = 0.625
TWO_WORD_STAKE_PERCENT = 0.3125
ONE_WORD_STAKE_PERCENT = 0.0625

# Keep this many branches recurring, preferring the highest scoring ones.
BRANCH_PRUNE_COUNT = 5

def branch_pruner(trie):
    # Base condition: if trie is not a dictionary, return immediately (no further branches to prune)
    if not isinstance(trie, dict):
        return
    
    # Iterate through each key in the trie
    for key in list(trie.keys()):
        # Recursively prune the branches of each subtree
        branch_pruner(trie[key])
    
    # If the current level contains '\ranked', start pruning based on BRANCH_PRUNE_COUNT
    if '\ranked' in trie:
        ranked_keys = trie['\ranked']
        # Determine the keys to keep: top BRANCH_PRUNE_COUNT keys based on the order in '\ranked'
        keys_to_keep = set(ranked_keys[:BRANCH_PRUNE_COUNT])
        
        # Add '\ranked' to the keys to keep to avoid pruning it
        keys_to_keep.add('\ranked')
        
        # Prune the keys not in keys_to_keep
        for key in list(trie.keys()):
            if key not in keys_to_keep:
                del trie[key]
                
        # Update the '\ranked' list to reflect the pruned keys
        trie['\ranked'] = ranked_keys[:BRANCH_PRUNE_COUNT]

def convert_to_array(obj):
    """
    Recursively converts dictionary objects to the specified array format, ensuring each string ends with a space.
    This function skips any keys named '\ranked'.
    """
    result = []
    for key, value in obj.items():
        # Skip the key if it is '\ranked'
        if key == '\ranked':
            continue
        key_with_space = key + " "  # Append a space to the key
        if isinstance(value, dict):
            # If the value is a dictionary, recursively process it
            child = convert_to_array(value)
            result.append([key_with_space, child])
        else:
            result.append(key_with_space)
    return result

def main(trie_store):
    # Path configuration is no longer needed for file paths but retained for logical separation
    # in trie_store
    output_file = 'dictionary.js'

    # Prune the dictionaries first
    prune_unpopular(trie_store, "3_words", target_dictionary_count=int(TARGET_DICTIONARY_COUNT * THREE_WORD_STAKE_PERCENT))
    prune_unpopular(trie_store, "2_words", target_dictionary_count=int(TARGET_DICTIONARY_COUNT * TWO_WORD_STAKE_PERCENT))
    prune_unpopular(trie_store, "1_word", target_dictionary_count=int(TARGET_DICTIONARY_COUNT * ONE_WORD_STAKE_PERCENT))

    # Initialize the dictionary object
    dictionary = {}

    print("Getting all dictionaries...")
    # Iterate over trie_store's sub-keys instead of .pkl files
    for dictionary_key in ["3_words", "2_words", "1_word"]:
        for slug, trie in trie_store['tries'].get(dictionary_key, {}).items():
            # Directly use trie from trie_store for conversion
            dictionary[slug] = convert_to_array(trie)

    print(f"Dictionary width is {len(dictionary.keys())}")
    # Write the dictionary object to dictionary.js in the desired format
    with open(output_file, 'w') as js_file:
        minimized_json = json.dumps(dictionary, separators=(',', ':'))
        js_content = f"export const dictionary = {minimized_json};"
        js_file.write(js_content)

def prune_unpopular(trie_store, dictionary_key, target_dictionary_count=TARGET_DICTIONARY_COUNT):
    # Directly access scores and tries from trie_store using dictionary_key
    scores = {k: v for k, v in trie_store['scores'].items() if k.startswith(dictionary_key)}

    print(f"\nStopping to prune least popular entries down to target dictionary size of %s..." % target_dictionary_count)

     # Sort scores by value in descending order and get the top_n keys
    top_slugs = sorted(scores, key=scores.get, reverse=True)[:target_dictionary_count]
    
    # Prune the tries and scores not in top_slugs within the specific dictionary_key
    for slug in list(trie_store['tries'][dictionary_key].keys()):
        if slug not in top_slugs:
            del trie_store['tries'][dictionary_key][slug]
            if slug in trie_store['scores']:
                del trie_store['scores'][slug]
    
    # Apply branch pruning to each trie in top_slugs within the specific dictionary_key
    for slug in top_slugs:
        trie = trie_store['tries'][dictionary_key].get(slug, {})
        branch_pruner(trie)
        # Since the trie is directly modified in-place, no need to "save" it back   

if __name__ == "__main__":
    main()