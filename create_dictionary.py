import os
import pickle
import json

# Assuming prune_unpopular is defined in train.py and is importable
from train import prune_unpopular

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

if __name__ == "__main__":
    main()