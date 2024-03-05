import os
import json

def main(trie_store, TARGET_DICTIONARY_COUNT):
    output_file_anchors = 'dictionary-anchors.js'
    output_file_properties = 'dictionary-properties.js'

    # Initialize containers for the new structures
    anchors = {}
    properties = {}

    # Iterate through each item in trie_store["fingerprints"]
    for context_group, info in trie_store["fingerprints"].items():
        # Process anchors
        for anchor_word in info.get("anc", {}).keys():
            # If the anchor_word is not in anchors, initialize it with an empty list
            if anchor_word not in anchors:
                anchors[anchor_word] = []
            # Append the context_group to the anchor_word's list
            anchors[anchor_word].append(context_group)

        # Process properties excluding 'anc'
        properties[context_group] = {k: v for k, v in info.items() if k != "anc"}

    print(f"Dictionary width is {len(properties.keys())}")

    # Write the anchors object to dictionary-anchors.js in the desired format
    with open(output_file_anchors, 'w') as js_file:
        minimized_json = json.dumps(anchors, separators=(',', ':'))
        js_content = f"export const dictionary_anchors = {minimized_json};"
        js_file.write(js_content)

    # Write the properties object to dictionary-properties.js in the desired format
    with open(output_file_properties, 'w') as js_file:
        minimized_json = json.dumps(properties, separators=(',', ':'))
        js_content = f"export const dictionary_properties = {minimized_json};"
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