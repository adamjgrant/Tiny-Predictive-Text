# Import necessary modules
import os
import sys
import shutil
from tqdm import tqdm
from slugify import slugify
import string
from create_dictionary import main as flatten_to_dictionary
import signal
import pickle

###########
# RECIPES #
###########
# All with chunk size of 1024
# ?.?MB: Target dictionary count 100,000, Prune 10,000,000
# 8.5MB: Target dictionary count 25,000,  Prune 10,000,000
# 3.6MB: Target dictionary count 10,000,  Prune 10,000,000

PRUNE_FREQUENCY = 10 * 1000 * 1000 # Every this many document positions
CHUNK_SIZE = 1024 # 1KB per chunk
TARGET_DICTIONARY_COUNT = 10 * 1000 * 1000

# Define a flag to indicate when an interrupt has been caught
interrupted = False

# Used to calculate PRUNE_FREQUENCY against the current position
prune_position_marker = 0

def signal_handler(sig, frame):
    global interrupted
    interrupted = True
    print("Graceful exit request received.")

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)

def save_trie_store(trie_store):
    with open('training/trie_store.pkl', 'wb') as f:
        pickle.dump(trie_store, f, protocol=pickle.HIGHEST_PROTOCOL)
    print("trie_store saved due to interruption.")

DEFAULT_TRIE_STORE ={'tries': {'3_words': {}, '2_words': {}, '1_word': {}}, 'scores': {}} 

def load_trie_store():
    try:
        with open('training/trie_store.pkl', 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return DEFAULT_TRIE_STORE

# Define a function to slugify context words into a filename-safe string
def _slugify(text):
    return slugify(text, separator="_")

# Define a function to update the trie structure with predictive words
def update_trie(trie, predictive_words):
    for word in predictive_words:
        # Ensure each word has a sub-trie if it does not exist
        if word not in trie:
            trie[word] = {}

        # Ensure the '\ranked' key exists at the current level if not already present
        if '\ranked' not in trie:
            trie['\ranked'] = {}

        # Update the score in '\ranked' at the current level for the current word
        trie['\ranked'][word] = trie['\ranked'].get(word, 0) + 1
        
        # Move to the sub-trie of the current word for the next iteration
        # This ensures the structure for subsequent words while keeping '\ranked' updated at the parent level
        trie = trie[word]

# Define a function to load or initialize the trie from memory
def load_trie(trie_store, path, context_slug):
    # Access the trie data by first navigating to the path, then the context_slug
    return trie_store['tries'].get(path, {}).get(context_slug, {})

def save_trie(trie_store, trie, path, context_slug):
    # Check if the path exists in 'tries'; if not, create it
    if path not in trie_store['tries']:
        trie_store['tries'][path] = {}
    
    # Now, path exists for sure; check for context_slug under this path
    # This step might be redundant if you're always going to assign a new trie,
    # but it's crucial if you're updating or merging with existing data.
    if context_slug not in trie_store['tries'][path]:
        trie_store['tries'][path][context_slug] = {}

    # Assign the trie to the specified path and context_slug
    trie_store['tries'][path][context_slug] = trie

def update_scores(trie_store, path, context_slug):
    if path not in trie_store['scores']:
        trie_store['scores'][path] = {}
    if context_slug not in trie_store['scores'][path]:
        trie_store['scores'][path][context_slug] = 0
    trie_store['scores'][path][context_slug] += 1

def save_position(progress_file, current_position, trie_store):
  # Every now and then save our progress.
  print(f"Saving the current position of %s" % current_position)
  # Save the current progress (file position)
  with open(progress_file, 'w') as f:
      f.write(str(current_position))
  print(f"Passed %s positions. Time to optimize before continuing..." % PRUNE_FREQUENCY)
  flatten_to_dictionary(trie_store, TARGET_DICTIONARY_COUNT)

# Define a main function to orchestrate the training process
def main():
  global prune_position_marker

  # Parse command line arguments to get the name of the training data file
  if len(sys.argv) < 2:
        print("Usage: python train.py <name of training data>.txt")
        sys.exit(1)
  training_data_file = sys.argv[1]
  retain_data = '--retain' in sys.argv

  # If retain flag is set, try to load existing training data
  if retain_data:
      trie_store = load_trie_store()
      print("Retained data loaded.")
  else:
      # If not retaining data, clear existing training directory and start fresh
      trie_store = DEFAULT_TRIE_STORE
      if os.path.exists('training'):
          shutil.rmtree('training')
      print("Previous training data cleared.")
      trie_store = {'tries': {'3_words': {}, '2_words': {}, '1_word': {}}, 'scores': {}}
  
  # Get the total size of the file to calculate the number of iterations needed
  total_size = os.path.getsize(training_data_file)
  total_iterations = total_size // CHUNK_SIZE + (1 if total_size % CHUNK_SIZE > 0 else 0)

  # Ensure the 'training' directory and its subdirectories/files exist
  dictionaries_path = 'training/dictionaries'
  os.makedirs(dictionaries_path, exist_ok=True)
  os.makedirs(os.path.join(dictionaries_path, "3_words"), exist_ok=True)
  os.makedirs(os.path.join(dictionaries_path, "2_words"), exist_ok=True)
  os.makedirs(os.path.join(dictionaries_path, "1_word"), exist_ok=True)

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
      prune_position_marker = file.tell()

      with tqdm(initial=last_processed_position // CHUNK_SIZE, total=total_iterations, unit='chunk', desc="Processing file") as pbar:
          while True:
              current_position = file.tell()
              row = file.read(CHUNK_SIZE)
              if not row:
                  break
              
              pbar.update(1)

              words = row.split()

              if interrupted:
                print("Saving data. Script will terminate when done.")
                save_trie_store(trie_store)
                sys.exit(0)

              # Every now and then, prune unpopular entries.
              if (current_position - prune_position_marker > PRUNE_FREQUENCY):
                save_position(progress_file, current_position, trie_store)
                prune_position_marker = current_position

              # Process words three at a time with shifting window
              for i in range(len(words) - 2):
                  context_words = words[i:i+3]
                  predictive_words = []

                  # Determine predictive words, up to three or until one ends with a punctuation mark
                  for j in range(i + 3, min(i + 6, len(words))):
                      word = words[j]
                      # Define a set of punctuation that is allowed within a word
                      internal_punctuation = {"'", "-"}
                      # Create a set of punctuation that signals the end of a word, excluding the internal punctuation
                      ending_punctuation = set(string.punctuation) - internal_punctuation
                      
                      # Check for and remove ending punctuation from the word
                      cleaned_word = ''.join(char for char in word if char not in ending_punctuation)
                      
                      # If after cleaning the word it ends with any ending punctuation, or if the original word contained ending punctuation
                      if cleaned_word != word or any(char in ending_punctuation for char in word):
                          predictive_words.append(cleaned_word)
                          break
                      else:
                          # For regular words or words with internal punctuation, add the cleaned word
                          predictive_words.append(cleaned_word)

                  if not predictive_words:  # Skip if there are no predictive words
                      continue
                    
                  finish_filing(trie_store, context_words, predictive_words, "3_words")

                  ## Two word alternative
                  context_words_2 = words[i+1:i+3]
                  predictive_words_2 = predictive_words[:2]
                  finish_filing(trie_store, context_words_2, predictive_words_2, "2_words")

                  ## Three word alternative
                  context_words_1 = words[i+2:i+3]
                  finish_filing(trie_store, context_words_1, predictive_words_2, "1_word")
  flatten_to_dictionary(trie_store, TARGET_DICTIONARY_COUNT) 

def finish_filing(trie_store, context_words, predictive_words, dictionary_subpath):
    # Slugify the context words
    context_slug = _slugify('_'.join(context_words))

    # Now you can safely proceed with the trie file path
    trie = load_trie(trie_store, dictionary_subpath, context_slug)
    
    # Update the trie with the predictive words
    update_trie(trie, predictive_words)
    
    # Save the updated trie back to the .pkl file
    save_trie(trie_store, trie, dictionary_subpath, context_slug)
    
    # Update the counts in scores_3_words.pkl for the context words slug
    update_scores(trie_store, dictionary_subpath, context_slug) 

# Check if the script is being run directly and call the main function
if __name__ == "__main__":
    main()