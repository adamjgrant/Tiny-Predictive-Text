# Import necessary modules
import os
import sys
import shutil
from tqdm import tqdm
from slugify import slugify
import signal
import pickle
from lib.process_predictive_words import main as process_predictive_words
from lib.process_context_words import main as process_context_words
from lib.finish_filing import main as finish_filing
from lib.create_dictionary import create_dictionary_and_tokenize

###########
# RECIPES #
###########
# All with chunk size of 1024
# ??.?MB: Target dictionary count 250,000,   Prune 1,000,000
# 33.7MB: Target dictionary count 100,000,   Prune 1,000,000
# 11.9MB: Target dictionary count 25,000,    Prune 10,000,000
# 5.4MB:  Target dictionary count 10,000,    Prune 10,000,000

PRUNE_FREQUENCY = 1000 # Every this many document positions
CHUNK_SIZE = 1024 # 1KB per chunk
TARGET_DICTIONARY_COUNT = 10 * 1000

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

def save_tree_store(tree_store):
    with open('training/tree_store.pkl', 'wb') as f:
        pickle.dump(tree_store, f, protocol=pickle.HIGHEST_PROTOCOL)
    print("tree_store saved due to interruption.")

DEFAULT_TREE_STORE ={} 

def load_tree_store():
    try:
        with open('training/tree_store.pkl', 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return DEFAULT_TREE_STORE

def save_position(progress_file, current_position, tree_store):
  # Every now and then save our progress.
  print(f"Saving the current position of %s" % current_position)
  # Save the current progress (file position)
  with open(progress_file, 'w') as f:
      f.write(str(current_position))
  print(f"Passed %s positions. Time to optimize before continuing..." % PRUNE_FREQUENCY)
  create_dictionary_and_tokenize(tree_store, TARGET_DICTIONARY_COUNT)

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
      tree_store = load_tree_store()
      print("Retained data loaded.")
  else:
      # If not retaining data, clear existing training directory and start fresh
      tree_store = DEFAULT_TREE_STORE
      if os.path.exists('training'):
          shutil.rmtree('training')
      print("Previous training data cleared.")
  
  # Get the total size of the file to calculate the number of iterations needed
  total_size = os.path.getsize(training_data_file)
  total_iterations = total_size // CHUNK_SIZE + (1 if total_size % CHUNK_SIZE > 0 else 0)

  # Ensure the 'training' directory and its subdirectories/files exist
  dictionaries_path = 'training/dictionaries'
  os.makedirs(dictionaries_path, exist_ok=True)

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
      # Initialize the chunk processed counter for pruning logic
      chunks_processed_since_prune = 0

      with tqdm(initial=last_processed_position // CHUNK_SIZE, total=total_iterations, unit='chunk', desc="Processing file") as pbar:
          while True:
              row = file.read(CHUNK_SIZE)
              if not row:
                  break
              
              pbar.update(1)
              words = row.split()

              if interrupted:
                  print("Saving data. Script will terminate when done.")
                  save_tree_store(tree_store)
                  sys.exit(0)

              # - is a reserved character for storing scores.
              words = [word.replace("-", "\-") for word in words]
              words = [word.replace("_", "\_") for word in words]
              
              # Process words three at a time with shifting window
              for i in range(len(words) - 2):
                  context_words = process_context_words(words, i)
                  predictive_words = process_predictive_words(words, i)

                  if not predictive_words:  # Skip if there are no predictive words
                      continue

                  # It's better to tokenize on the create dictionary step so we're not
                  # tokenizing words that we don't end up needing. Create dict will make a fresh
                  # token dict on each run.
                  tree_store = finish_filing(tree_store, context_words, predictive_words)

              chunks_processed_since_prune += 1  # Increment chunk processed counter

              # Every now and then, prune unpopular entries based on chunks processed
              if chunks_processed_since_prune >= PRUNE_FREQUENCY:
                  save_position(progress_file, file.tell(), tree_store)
                  # Reset chunk processed counter after pruning
                  chunks_processed_since_prune = 0


  create_dictionary_and_tokenize(tree_store, TARGET_DICTIONARY_COUNT)

# Check if the script is being run directly and call the main function
if __name__ == "__main__":
    main()