import os
import pickle
import json

# Assuming prune_unpopular is defined in train.py and is importable
from train import prune_unpopular

def convert_to_array(obj):
    """
    Recursively converts dictionary objects to the specified array format.
    """
    result = []
    for key, value in obj.items():
        if isinstance(value, dict):
            # If the value is a dictionary, recursively process it
            child = convert_to_array(value)
            result.append([key, child])
        else:
            result.append(key)
    return result

def main():
    # Path configuration
    dictionaries_path = 'training/dictionaries'
    scores_file_path = 'training/scores.pkl'
    output_file = 'dictionary.js'

    # Prune the dictionaries first
    prune_unpopular(scores_file_path, dictionaries_path)

    # Initialize the dictionary object
    dictionary = {}

    # Iterate over every .pkl file in the dictionaries directory
    print("Getting all dictionaries...")
    for filename in os.listdir(dictionaries_path):
        if filename.endswith('.pkl'):
            slug, _ = os.path.splitext(filename)
            file_path = os.path.join(dictionaries_path, filename)
            
            with open(file_path, 'rb') as file:
                trie = pickle.load(file)
                # Convert trie to the specified array format
                dictionary[slug] = convert_to_array(trie)

    print(f"Dictionary length is %s" % dictionary.keys().__len__())
    # Write the dictionary object to dictionary.js in the desired format
    with open(output_file, 'w') as js_file:
        # Minimize by removing unnecessary whitespace in json.dumps and adjusting js_content formatting
        minimized_json = json.dumps(dictionary, separators=(',', ':'))
        js_content = f"const dictionary={minimized_json};\nexports.dictionary=dictionary;"
        js_file.write(js_content)

if __name__ == "__main__":
    main()