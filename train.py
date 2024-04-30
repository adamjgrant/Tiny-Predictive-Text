# Import necessary modules
import os
import sys
import shutil
from tqdm import tqdm
import signal
import datasets
import logging
from lib.process_predictive_words import main as process_predictive_words
from lib.process_context_words import main as process_context_words
from lib.finish_filing import main as finish_filing
from lib.create_dictionary import create_batch
from lib.merge_batches import main as merge_batches
import asyncio
import gc
from lib.constants import PRUNE_FREQUENCY, TARGET_DICTIONARY_COUNT, TOTAL_WORD_COUNT
import argparse  # Import argparse for command-line parsing

# Define a flag to indicate when an interrupt has been caught
interrupted = False

def signal_handler(sig, frame):
    global interrupted
    interrupted = True
    print("Graceful exit request received.")

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)

DEFAULT_TREE_STORE ={} 

async def save_position(progress_file, current_position, word_count, tree_store):
  # Every now and then save our progress.
  print(f"Saving the current position of %s" % current_position)

  # Save the current progress (file position)
  with open(progress_file, 'w') as f:
      f.write(f"{str(current_position)},{str(word_count)}")

  print(f"Passed %s positions. Time to optimize before continuing..." % PRUNE_FREQUENCY)
  await create_batch(tree_store, TARGET_DICTIONARY_COUNT)
  return DEFAULT_TREE_STORE

async def main(retain=False):
  tree_store = DEFAULT_TREE_STORE
  if not retain and os.path.exists('training'):
      shutil.rmtree('training')
      print("Previous training data cleared.")

  training_path = 'training'
  os.makedirs(training_path, exist_ok=True)

  # Load dataset from Hugging Face datasets
  datasets.logging.set_verbosity(datasets.logging.WARNING)
  logging.getLogger('fsspec').setLevel(logging.WARNING)
  logging.getLogger('urllib3').setLevel(logging.WARNING)
  dataset = datasets.load_dataset('oscar-corpus/OSCAR-2201', language='en', split='train', streaming=True, trust_remote_code=True)
  
  # Initialize start_position and word_length to 0
  start_position = 0
  word_count = 0

  # Check if the --retain flag is used and if the progress file exists
  if retain and os.path.exists('training/processing_progress.txt'):
      with open('training/processing_progress.txt', 'r') as f:
          # Read the line and split it by the comma to get both values
          start_position_str, word_length_str = f.read().strip().split(',')
          # Convert the string values to integers
          start_position = int(start_position_str)
          word_count = int(word_length_str)
          print(f"Resuming from position {start_position} with {word_count} total words processed.")

  pbar = tqdm(total=TOTAL_WORD_COUNT, unit='word', desc="Processing dataset", position=1)
  pbar.update(word_count)
  for i, entry in enumerate(dataset.skip(start_position)):
      if i + start_position < start_position:
          pbar.display(f"Skipping ahead from {i + start_position} to {start_position}", 1)
          continue  # Skip to the saved position
      text = entry['text']  # Extract text from dataset entry
      words = text.split()

      pbar.update(len(words))

      # Replace reserved characters as before
      words = [word.replace("score", "\sscore") for word in words]
      words = [word.replace("prediction", "\sprediction") for word in words]

      # Process words three at a time with shifting window
      for j in range(len(words) - 2):
          word_count += 1
          if interrupted:
              print("Script will terminate when done.")
              sys.exit(0)

          context_words = process_context_words(words, j)
          predictive_words = process_predictive_words(words, j)

          if not predictive_words:
              continue

          tree_store = finish_filing(tree_store, context_words, predictive_words)

          if (word_count + 1) % PRUNE_FREQUENCY == 0:
              # Save position and prune every PRUNE_FREQUENCY entries
              tree_store = await save_position('training/processing_progress.txt', i + start_position + 1, word_count, tree_store)
              gc.collect()

          if (word_count + 1) % (PRUNE_FREQUENCY * 10) == 0:
              merge_batches()
            
  await create_batch(tree_store, TARGET_DICTIONARY_COUNT)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Training script with position retain functionality.')
    parser.add_argument('--retain', action='store_true', help='Retain and resume from last saved position.')
    args = parser.parse_args()
    
    asyncio.run(main(retain=args.retain))
