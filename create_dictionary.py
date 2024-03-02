import os
import pickle
import json

# Assuming prune_unpopular is defined in train.py and is importable
TARGET_DICTIONARY_COUNT = 10000 

def convert_to_array(obj):
    """
    Recursively converts dictionary objects to the specified array format, ensuring each string ends with a space.
    """
    result = []
    for key, value in obj.items():
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
    prune_unpopular(scores_3_words_file_path, os.path.join(dictionaries_path, "3_words"))
    prune_unpopular(scores_2_words_file_path, os.path.join(dictionaries_path, "2_words"), target_dictionary_count=5000)
    prune_unpopular(scores_1_word_file_path, os.path.join(dictionaries_path, "1_word"), target_dictionary_count=1000)

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
        if slug not in top_slugs_set:
            # This file is not among the top scoring, so delete it
            os.remove(os.path.join(dictionaries_path, filename))
            slugs_to_remove.append(slug)

    # Remove the pruned entries from scores
    for slug in slugs_to_remove:
        if slug in scores:
            del scores[slug]

if __name__ == "__main__":
    main()