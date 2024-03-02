# Import necessary modules
import os
import sys
import pickle
import re
from collections import defaultdict
import shutil
from tqdm import tqdm
from slugify import slugify
from create_dictionary import main as flatten_to_dictionary

PRUNE_FREQUENCY = 25000

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

# Define a main function to orchestrate the training process
def main():
  # We'll try to create this many dictionaries by frequently pruning 20% of the least popular entries.

  # Parse command line arguments to get the name of the training data file
  if len(sys.argv) < 2:
        print("Usage: python train.py <name of training data>.txt")
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
  scores_3_words_file_path = 'training/scores_3_words.pkl'
  scores_2_words_file_path = 'training/scores_2_words.pkl'
  scores_1_word_file_path = 'training/scores_1_word.pkl'

  # Set each score file with an empty object if they don't exist.
  for path in [scores_1_word_file_path, scores_2_words_file_path, scores_3_words_file_path]:
    if not os.path.exists(path):
        with open(path, 'wb') as scores_file:
            pickle.dump({}, scores_file, protocol=pickle.HIGHEST_PROTOCOL)

  # Read the TXT file and process the training data
  chunk_size = 1024 * 1024  # 1MB per chunk

  # Get the total size of the file to calculate the number of iterations needed
  total_size = os.path.getsize(training_data_file)
  total_iterations = total_size // chunk_size + (1 if total_size % chunk_size > 0 else 0)

  # Open the file and process it in chunks with tqdm progress bar
  with open(training_data_file, 'r') as file:
      iteration_count = 0  # Now and then we'll prune unpopular entries.
      with tqdm(total=total_iterations, unit='chunk', desc="Processing file") as pbar:
          while True:
              row = file.read(chunk_size)
              if not row:
                  break
              iteration_count += 1
              pbar.update(1)

              words = row.split()
              # Process words three at a time with shifting window
              for i in range(len(words) - 2):
                  context_words = words[i:i+3]
                  predictive_words = []
                  iteration_count += 1

                  # Every now and then, prune unpopular entries.
                  if iteration_count % PRUNE_FREQUENCY == 0:
                    flatten_to_dictionary()

                  # Determine predictive words, up to three or until a punctuation mark
                  for j in range(i + 3, min(i + 6, len(words))):
                      if words[j] in ['.', ',', '\n', '\r', '\r\n']:
                          break
                      predictive_words.append(words[j])
                  if not predictive_words:  # Skip if there are no predictive words
                      continue
                    
                  finish_filing(context_words, predictive_words, scores_3_words_file_path, "3_words")

                  ## Two word alternative
                  context_words_2 = words[i+1:i+3]
                  predictive_words_2 = predictive_words[:2]
                  finish_filing(context_words_2, predictive_words_2, scores_2_words_file_path, "2_words")

                  ## Three word alternative
                  context_words_1 = words[i+2:i+3]
                  finish_filing(context_words_1, predictive_words_2, scores_1_word_file_path, "1_word")
  
def finish_filing(context_words, predictive_words, scores_file_path, dictionary_subpath):
    # Slugify the context words
    context_slug = _slugify('_'.join(context_words))
    
    # Before loading or initializing the trie, ensure the directory exists
    dictionary_directory = os.path.join('training/dictionaries', dictionary_subpath)
    os.makedirs(dictionary_directory, exist_ok=True)

    # Now you can safely proceed with the trie file path
    trie_file_path = os.path.join(dictionary_directory, f'{context_slug}.pkl')
    trie = load_trie(trie_file_path)
    
    # Update the trie with the predictive words
    update_trie(trie, predictive_words)
    
    # Save the updated trie back to the .pkl file
    save_trie(trie, trie_file_path)
    
    # Update the counts in scores_3_word.pkl for the context words slug
    update_scores(scores_file_path, context_slug) 

# Check if the script is being run directly and call the main function
if __name__ == "__main__":
    main()