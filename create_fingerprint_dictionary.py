import os
import json

def main(trie_store, TARGET_DICTIONARY_COUNT):
    output_file_anchors = 'dictionary-anchors.js'
    output_file_properties = 'dictionary-properties.js'
    output_file_token_mapping = 'token-mapping.js'

    # Initialize containers for the new structures
    anchors = {}
    properties = {}
    word_to_token = {}
    token_to_word = {}
    token_counter = 1  # Start token counter

    prune_unpopular(trie_store, TARGET_DICTIONARY_COUNT)

    # Process properties and tokenize 'completion' phrases
    for context_group, info in trie_store["fingerprints"].items():
        completion = info.get("completion", "")
        tokenized_completion = []
        
        # Tokenize each word in the completion phrase
        for word in completion.split():
            if word not in word_to_token:
                word_to_token[word] = token_counter
                token_to_word[token_counter] = word
                token_counter += 1
            tokenized_completion.append(str(word_to_token[word]))
        
        # Reconstruct the completion phrase using tokens
        tokenized_completion_str = " ".join(tokenized_completion)

        # Process anchors
        for anchor_word in info.get("anc", {}).keys():
            if anchor_word not in word_to_token:
                word_to_token[anchor_word] = token_counter
                token_to_word[token_counter] = anchor_word
                token_counter += 1
            token = word_to_token[anchor_word]
            if token not in anchors:
                anchors[token] = []
            anchors[token].append(context_group)
        
        # Store tokenized completion in properties excluding 'anc'
        info["completion"] = tokenized_completion_str
        properties[context_group] = {k: v for k, v in info.items() if k != "anc"}

    # Export the new structures to JavaScript files
    write_to_js(output_file_anchors, anchors, "dictionary_anchors")
    write_to_js(output_file_properties, properties, "dictionary_properties")
    write_to_js(output_file_token_mapping, token_to_word, "token_mapping")

def write_to_js(file_path, data, variable_name):
    with open(file_path, 'w') as js_file:
        minimized_json = json.dumps(data, separators=(',', ':'))
        js_content = f"export const {variable_name} = {minimized_json};"
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