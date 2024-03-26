# Import necessary modules
import os
import sys
import shutil
from tqdm import tqdm
import signal
import pickle
from datasets import load_dataset
from lib.process_predictive_words import main as process_predictive_words
from lib.process_context_words import main as process_context_words
from lib.finish_filing import main as finish_filing
from lib.create_dictionary import create_dictionary_and_tokenize
import asyncio
import gc

###########
# RECIPES #
###########
# All with chunk size of 1024
# 1.4MB: Target dictionary count 9 * 1000,   Prune 4 * 1000

PRUNE_FREQUENCY = 8 * 1000 # Every this many chunks
CHUNK_SIZE = 1024 # 1KB per chunk
TARGET_DICTIONARY_COUNT = 100

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
    return # TODO Not working
    with open('training/tree_store.pkl', 'wb') as f:
        pickle.dump(tree_store, f, protocol=pickle.HIGHEST_PROTOCOL)
    print("tree_store saved due to interruption.")

DEFAULT_TREE_STORE ={} 

def load_tree_store():
    return # TODO Not working
    try:
        with open('training/tree_store.pkl', 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return DEFAULT_TREE_STORE

async def save_position(progress_file, current_position, tree_store):
  # Every now and then save our progress.
  print(f"Saving the current position of %s" % current_position)
  # Save the current progress (file position)
  with open(progress_file, 'w') as f:
      f.write(str(current_position))
  print(f"Passed %s positions. Time to optimize before continuing..." % PRUNE_FREQUENCY)
  tree_store = await create_dictionary_and_tokenize(tree_store, TARGET_DICTIONARY_COUNT)
  return tree_store

# Define a main function to orchestrate the training process
async def main():
  global prune_position_marker

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

  # Load dataset from Hugging Face datasets
  # dataset = load_dataset("EleutherAI/pile", split='train') # Defunct :(
  dataset = load_dataset("gmongaras/EleutherAI_the_pile_deduplicated", split='train')
  total_iterations = len(dataset)  # Total entries in the dataset
  
  # Ensure the 'training' directory and its subdirectories/files exist
  dictionaries_path = 'training/dictionaries'
  os.makedirs(dictionaries_path, exist_ok=True)

  # Define a file to store the progress
  progress_file = 'training/processing_progress.txt'

  # Check if progress file exists and read the last processed byte position
  if os.path.exists(progress_file):
      with open(progress_file, 'r') as f:
          last_processed_position = int(f.read().strip())
  else:
      last_processed_position = 0

  with tqdm(total=total_iterations, unit='entry', desc="Processing dataset") as pbar:
      for i, entry in enumerate(dataset):
          text = entry['text']  # Extract text from dataset entry
          words = text.split() 

          # Replace reserved characters as before
          words = [word.replace("score", "\sscore") for word in words]
          words = [word.replace("prediction", "\sprediction") for word in words]

          # Process words three at a time with shifting window
          for j in range(len(words) - 2):
              if interrupted:
                  print("Saving data. Script will terminate when done.")
                  save_tree_store(tree_store)
                  sys.exit(0)

              context_words = process_context_words(words, j)
              predictive_words = process_predictive_words(words, j)

              if not predictive_words:
                  continue

              # It's better to tokenize on the create dictionary step so we're not
              # tokenizing words that we don't end up needing. Create dict will make a fresh
              # token dict on each run.
              tree_store = finish_filing(tree_store, context_words, predictive_words)

          pbar.update(1)

          if (i + 1) % PRUNE_FREQUENCY == 0:
              # Save position and prune every PRUNE_FREQUENCY entries
              tree_store = await save_position('training/processing_progress.txt', i + 1, tree_store)
              gc.collect()
            
      await create_dictionary_and_tokenize(tree_store, TARGET_DICTIONARY_COUNT)

# Check if the script is being run directly and call the main function
if __name__ == "__main__":
    asyncio.run(main())