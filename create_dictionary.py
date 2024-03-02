import os
import pickle
import json

# Across all dictionaries, how many entry word sets total should we regularly prune the 
# dictionary back to contain?
TARGET_DICTIONARY_COUNT = 16000 

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

def main():
    # Path configuration
    dictionaries_path = 'training/dictionaries'
    scores_3_words_file_path = 'training/scores_3_words.pkl'
    scores_2_words_file_path = 'training/scores_2_words.pkl'
    scores_1_word_file_path = 'training/scores_1_word.pkl'
    output_file = 'dictionary.js'

    # Prune the dictionaries first
    prune_unpopular(scores_3_words_file_path, os.path.join(dictionaries_path, "3_words"), target_dictionary_count=int(TARGET_DICTIONARY_COUNT * THREE_WORD_STAKE_PERCENT))
    prune_unpopular(scores_2_words_file_path, os.path.join(dictionaries_path, "2_words"), target_dictionary_count=int(TARGET_DICTIONARY_COUNT * TWO_WORD_STAKE_PERCENT))
    prune_unpopular(scores_1_word_file_path, os.path.join(dictionaries_path, "1_word"), target_dictionary_count=int(TARGET_DICTIONARY_COUNT * ONE_WORD_STAKE_PERCENT))

    # Initialize the dictionary object
    dictionary = {}

    # Iterate over every .pkl file in the dictionaries directory
    # Define the subdirectories
    subdirectories = ["3_words", "2_words", "1_word"]

    print("Getting all dictionaries...")
    for subdirectory in subdirectories:
        # Construct the path to the subdirectory
        subdirectory_path = os.path.join(dictionaries_path, subdirectory)
        
        # Iterate over every .pkl file in the current subdirectory
        for filename in os.listdir(subdirectory_path):
            if filename.endswith('.pkl'):
                slug, _ = os.path.splitext(filename)
                file_path = os.path.join(subdirectory_path, filename)
                
                with open(file_path, 'rb') as file:
                    trie = pickle.load(file)
                    # Convert trie to the specified array format
                    # Use a modified slug that includes the subdirectory name for uniqueness
                    dictionary[slug] = convert_to_array(trie)

    print(f"Dictionary length is %s" % dictionary.keys().__len__())
    # Write the dictionary object to dictionary.js in the desired format
    with open(output_file, 'w') as js_file:
        # Minimize by removing unnecessary whitespace in json.dumps and adjusting js_content formatting
        minimized_json = json.dumps(dictionary, separators=(',', ':'))
        js_content = f"export const dictionary = {minimized_json};"
        js_file.write(js_content)

def prune_unpopular(scores_file_path, dictionaries_path, target_dictionary_count=TARGET_DICTIONARY_COUNT):
    # Load the scores
    if os.path.exists(scores_file_path):
        with open(scores_file_path, 'rb') as file:
            scores = pickle.load(file)
    else:
        print("Scores file does not exist.")
        return

    print(f"\nStopping to prune least popular entries down to target dictionary size of %s..." % target_dictionary_count) 

    # Sort scores by value in descending order and get the top_n keys
    top_slugs = sorted(scores, key=scores.get, reverse=True)[:target_dictionary_count]

    # Convert to set for faster lookup
    top_slugs_set = set(top_slugs)

    # Track slugs to be removed from scores
    slugs_to_remove = []

    # Iterate over all files in dictionaries directory
    for filename in os.listdir(dictionaries_path):
        slug, ext = os.path.splitext(filename)
        full_path = os.path.join(dictionaries_path, filename)
        if slug not in top_slugs_set:
            # This file is not among the top scoring, so delete it
            os.remove(full_path)
            slugs_to_remove.append(slug)
        else:
          # Since we're keeping the file, let's prune its branches.
          with open(full_path, 'rb') as f:
              trie = pickle.load(f)
          
          # Apply branch pruning to the trie
          branch_pruner(trie)
          
          # Save the pruned trie back to the file
          with open(full_path, 'wb') as f:
              pickle.dump(trie, f, protocol=pickle.HIGHEST_PROTOCOL)

    # Remove the pruned entries from scores
    for slug in slugs_to_remove:
        if slug in scores:
            del scores[slug]

if __name__ == "__main__":
    main()