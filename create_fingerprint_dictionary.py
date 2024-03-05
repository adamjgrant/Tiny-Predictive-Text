import os
import json

def main(trie_store, TARGET_DICTIONARY_COUNT):
    # Path configuration is no longer needed for file paths but retained for logical separation
    # in trie_store
    output_file = 'dictionary-fingerprint.js'

    # Prune the dictionary first
    prune_unpopular(trie_store, target_dictionary_count=TARGET_DICTIONARY_COUNT)

    # Initialize the dictionary object
    dictionary = trie_store["fingerprints"]

    print(f"Dictionary width is {len(dictionary.keys())}")
    # Write the dictionary object to dictionary.js in the desired format
    with open(output_file, 'w') as js_file:
        minimized_json = json.dumps(dictionary, separators=(',', ':'))
        js_content = f"export const dictionary_fingerprint = {minimized_json};"
        js_file.write(js_content)

def prune_unpopular(trie_store, target_dictionary_count):
    # Access the nested scores directly
    scores = trie_store['scores']
    
    # Sort scores by value in descending order to identify top slugs
    top_slugs = sorted(scores, key=scores.get, reverse=True)[:target_dictionary_count]

    existing_slugs = set(trie_store['fingerprints'].keys())
    slugs_to_keep = set(top_slugs)
    slugs_to_prune = existing_slugs - slugs_to_keep

    # Prune the tries not in top slugs
    for slug in slugs_to_prune:
        del trie_store['fingerprints'][slug]
    
    # Optionally, prune scores not associated with top slugs
    for slug in slugs_to_prune:
        if slug in scores:
            del trie_store['scores'][slug]

if __name__ == "__main__":
    main()