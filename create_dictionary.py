import os
import json

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
    
    # Recursively prune the branches of each subtree
    for key in list(trie.keys()):
        if key != '\ranked':
            branch_pruner(trie[key])
    
    # If the current level contains '\ranked', start pruning based on BRANCH_PRUNE_COUNT
    if '\ranked' in trie:
        # Sort the ranked words by their scores in descending order and keep only the top BRANCH_PRUNE_COUNT words
        top_ranked_words = sorted(trie['\ranked'].items(), key=lambda item: item[1], reverse=True)[:BRANCH_PRUNE_COUNT]
        # Convert the list of tuples back to a dictionary
        top_ranked_dict = {word: score for word, score in top_ranked_words}

        # print(top_ranked_dict)
        
        # Prune the trie to keep only the branches corresponding to the top ranked words
        keys_to_keep = set(word for word, _ in top_ranked_words)
        keys_to_keep.add('\ranked')  # Ensure '\ranked' itself is kept
        
        for key in list(trie.keys()):
            if key not in keys_to_keep and key != '\ranked':
                del trie[key]  # Remove branches not among the top ranked

        # Update the '\ranked' dictionary to reflect only the top ranked words and their scores
        trie['\ranked'] = top_ranked_dict

def convert_to_array(obj):
    """
    Recursively converts dictionary objects to the specified array format, ensuring each string ends with a space.
    This function skips any keys named '\ranked' and filters out empty child arrays.
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
            # Append [key_with_space, child] only if child is not empty
            if child:  # This checks if child is non-empty
                result.append([key_with_space, child])
            else:  # If child is empty, append only the key
                result.append(key_with_space)
        else:
            result.append(key_with_space)
    return result

def main(trie_store, TARGET_DICTIONARY_COUNT):
    # Path configuration is no longer needed for file paths but retained for logical separation
    # in trie_store
    output_file = 'dictionary.js'

    # Prune the dictionaries first
    prune_unpopular(trie_store, "3_words", target_dictionary_count=int(TARGET_DICTIONARY_COUNT * THREE_WORD_STAKE_PERCENT))
    prune_unpopular(trie_store, "2_words", target_dictionary_count=int(TARGET_DICTIONARY_COUNT * TWO_WORD_STAKE_PERCENT))
    prune_unpopular(trie_store, "1_word", target_dictionary_count=int(TARGET_DICTIONARY_COUNT * ONE_WORD_STAKE_PERCENT))

    # Initialize the dictionary object
    dictionary = {}

    print("Taking everything we've compiled so far and re-minting a new dictionary.js...")
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

def prune_unpopular(trie_store, dictionary_key, target_dictionary_count):
    # Access the nested scores directly
    scores = trie_store['scores'].get(dictionary_key, {})
    
    # Sort scores by value in descending order to identify top slugs
    top_slugs = sorted(scores, key=scores.get, reverse=True)[:target_dictionary_count]

    existing_slugs = set(trie_store['tries'][dictionary_key].keys())
    slugs_to_keep = set(top_slugs)
    slugs_to_prune = existing_slugs - slugs_to_keep

    # Prune the tries not in top slugs
    for slug in slugs_to_prune:
        del trie_store['tries'][dictionary_key][slug]
    
    # Optionally, prune scores not associated with top slugs
    for slug in slugs_to_prune:
        if slug in scores:
            del trie_store['scores'][dictionary_key][slug]

    # Apply branch pruning to each trie in top slugs within the specific dictionary_key
    for slug in slugs_to_keep:
        trie = trie_store['tries'][dictionary_key].get(slug, {})
        branch_pruner(trie)

if __name__ == "__main__":
    main()