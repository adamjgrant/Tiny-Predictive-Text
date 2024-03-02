# Import necessary modules
import os
import sys
import pickle
import re
from collections import defaultdict
import csv
import shutil
from tqdm import tqdm
from slugify import slugify

# Define a function to slugify context words into a filename-safe string
def _slugify(text):
    return slugify(text, separator="_")

# Define a function to update the trie structure with predictive words
def update_trie(trie, predictive_words):
    for word in predictive_words:
        if word not in trie:
            trie[word] = {}
        trie = trie[word]

# Define a function to load or initialize the trie from a .pkl file
def load_trie(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            trie = pickle.load(file)
    else:
        trie = {}
    return trie

# Define a function to save the updated trie back to the .pkl file
def save_trie(trie, file_path):
    with open(file_path, 'wb') as file:
        pickle.dump(trie, file, protocol=pickle.HIGHEST_PROTOCOL)

# Define a function to update scores in scores.pkl
def update_scores(scores_file_path, context_slug):
    if os.path.exists(scores_file_path):
        with open(scores_file_path, 'rb') as file:
            scores = pickle.load(file)
    else:
        scores = {}
    
    scores[context_slug] = scores.get(context_slug, 0) + 1
    
    with open(scores_file_path, 'wb') as file:
        pickle.dump(scores, file, protocol=pickle.HIGHEST_PROTOCOL)

target_dictionary_count = 10000 

# Define a main function to orchestrate the training process
def main():
  # We'll try to create this many dictionaries by frequently pruning 20% of the least popular entries.

  # Parse command line arguments to get the name of the training data file
  if len(sys.argv) < 2:
        print("Usage: python train.py <name of training data>.csv")
        sys.exit(1)
  training_data_file = sys.argv[1]
  retain_data = '--retain' in sys.argv
  
  # If retain flag is not set, clear existing training data
  if not retain_data:
      if os.path.exists('training'):
          shutil.rmtree('training')
      print("Previous training data cleared.")
  
  # Ensure the 'training' directory and its subdirectories/files exist
  dictionaries_path = 'training/dictionaries'
  os.makedirs(dictionaries_path, exist_ok=True)
  scores_file_path = 'training/scores.pkl'
  if not os.path.exists(scores_file_path):
      with open(scores_file_path, 'wb') as scores_file:
          pickle.dump({}, scores_file, protocol=pickle.HIGHEST_PROTOCOL)

  # Read the CSV file and process the training data
  # Open the CSV file
  csv.field_size_limit(sys.maxsize)
  with open(training_data_file, 'r', newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    # Wrap reader in tqdm for a progress bar. Note: No total count provided.
    iteration_count = 0 # Now and then we'll prune unpopular entries.
    for row in tqdm(reader, desc="Processing CSV rows"):
        try:
            words = ' '.join(row).split()
            # Process words three at a time with shifting window
            for i in range(len(words) - 2):
                context_words = words[i:i+3]
                predictive_words = []
                iteration_count += 1

                # Every now and then, prune unpopular entries.
                if iteration_count % 100000 == 0:
                  prune_unpopular(scores_file_path, dictionaries_path)

                # Determine predictive words, up to three or until a punctuation mark
                for j in range(i + 3, min(i + 6, len(words))):
                    if words[j] in ['.', ',', '\n', '\r', '\r\n']:
                        break
                    predictive_words.append(words[j])
                if not predictive_words:  # Skip if there are no predictive words
                    continue
                  
                # Slugify the context words
                context_slug = _slugify('_'.join(context_words))
                
                # Load or initialize the trie for the context words from its .pkl file
                trie_file_path = os.path.join('training/dictionaries', f'{context_slug}.pkl')
                trie = load_trie(trie_file_path)
                
                # Update the trie with the predictive words
                update_trie(trie, predictive_words)
                
                # Save the updated trie back to the .pkl file
                save_trie(trie, trie_file_path)
                
                # Update the counts in scores.pkl for the context words slug
                update_scores(scores_file_path, context_slug)
        except csv.Error as e:
            print(f"Error processing row: {e}")
            # Optionally, log the error or take other actions
            continue  # Skip to the next row
  
  print("\nFinal pruning...")
  prune_unpopular(scores_file_path, dictionaries_path)

def prune_unpopular(scores_file_path, dictionaries_path):
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

# Check if the script is being run directly and call the main function
if __name__ == "__main__":
    main()