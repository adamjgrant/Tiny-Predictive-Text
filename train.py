# Import necessary modules
import os
import sys
import pickle
import re
from collections import defaultdict
import shutil
from tqdm import tqdm
from slugify import slugify
import string
from create_dictionary import main as flatten_to_dictionary
import signal

PRUNE_FREQUENCY = 250000 # Every this many document positions
CHUNK_SIZE = 1024 # 1KB per chunk

# Define a flag to indicate when an interrupt has been caught
interrupted = False

# Used to calculate PRUNE_FREQUENCY against the current position
prune_position_marker = 0

def signal_handler(sig, frame):
    global interrupted
    print('Signal received, cleaning up...')
    interrupted = True
    # Perform any necessary cleanup here
    # For example, save progress to file
    # save_progress()

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)

# Define a function to slugify context words into a filename-safe string
def _slugify(text):
    return slugify(text, separator="_")

# Define a function to update the trie structure with predictive words
def update_trie(trie, predictive_words):
    for word in predictive_words:
        if word not in trie:
            trie[word] = {}
            # Ensure the '\ranked' key exists with a default list if not already present
            if '\ranked' not in trie:
                trie['\ranked'] = []
            # Add the word to '\ranked' if it's not already in the list
            if word not in trie['\ranked']:
                trie['\ranked'].append(word)
            else:
                # Promote the word by one position if it's not already at the start
                index = trie['\ranked'].index(word)
                if index > 0:
                    trie['\ranked'].insert(max(0, index - 1), trie['\ranked'].pop(index))
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
  global prune_position_marker

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
  os.makedirs(os.path.join(dictionaries_path, "3_words"), exist_ok=True)
  os.makedirs(os.path.join(dictionaries_path, "2_words"), exist_ok=True)
  os.makedirs(os.path.join(dictionaries_path, "1_word"), exist_ok=True)
  scores_3_words_file_path = 'training/scores_3_words.pkl'
  scores_2_words_file_path = 'training/scores_2_words.pkl'
  scores_1_word_file_path = 'training/scores_1_word.pkl'

  # Set each score file with an empty object if they don't exist.
  for path in [scores_1_word_file_path, scores_2_words_file_path, scores_3_words_file_path]:
    if not os.path.exists(path):
        with open(path, 'wb') as scores_file:
            pickle.dump({}, scores_file, protocol=pickle.HIGHEST_PROTOCOL)

  # Read the TXT file and process the training data

  # Get the total size of the file to calculate the number of iterations needed
  total_size = os.path.getsize(training_data_file)
  total_iterations = total_size // CHUNK_SIZE + (1 if total_size % CHUNK_SIZE > 0 else 0)

  # Define a file to store the progress
  progress_file = 'training/processing_progress.txt'

  # Check if progress file exists and read the last processed byte position
  if os.path.exists(progress_file):
      with open(progress_file, 'r') as f:
          last_processed_position = int(f.read().strip())
  else:
      last_processed_position = 0

  # Open the file and process it in chunks with tqdm progress bar
  with open(training_data_file, 'r') as file:
      # Skip to the last processed position, if any
      file.seek(last_processed_position)

      with tqdm(initial=last_processed_position // CHUNK_SIZE, total=total_iterations, unit='chunk', desc="Processing file") as pbar:
          while True:
              current_position = file.tell()
              row = file.read(CHUNK_SIZE)
              if not row:
                  break
              
              pbar.update(1)

              words = row.split()

              # Every now and then save our progress.
              print(f"Saving the current position of %s" % current_position)
              # Save the current progress (file position)
              with open(progress_file, 'w') as f:
                  f.write(str(current_position))

              if interrupted:
                print("Interrupt detected, exiting loop...")
                sys.exit(0)

              # Process words three at a time with shifting window
              for i in range(len(words) - 2):
                  context_words = words[i:i+3]
                  predictive_words = []

                  # Every now and then, prune unpopular entries.
                  if (current_position - prune_position_marker > PRUNE_FREQUENCY):
                    prune_position_marker = current_position
                    print(f"Passed %s positions. Time to optimize before continuing..." % PRUNE_FREQUENCY)
                    flatten_to_dictionary()

                  # Determine predictive words, up to three or until one ends with a punctuation mark
                  for j in range(i + 3, min(i + 6, len(words))):
                      word = words[j]
                      # Define a set of punctuation that is allowed within a word
                      internal_punctuation = {"'", "-"}
                      # Create a set of punctuation that signals the end of a word, excluding the internal punctuation
                      ending_punctuation = set(string.punctuation) - internal_punctuation
                      
                      # Check if the last character of the word is in the set of ending punctuation
                      if word[-1] in ending_punctuation:
                          # If a word ends with an ending punctuation, add the word and break
                          predictive_words.append(word)
                          break
                      else:
                          # For regular words or words with internal punctuation, add the word
                          predictive_words.append(word)
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
    
    # Update the counts in scores_3_words.pkl for the context words slug
    update_scores(scores_file_path, context_slug) 

# Check if the script is being run directly and call the main function
if __name__ == "__main__":
    main()