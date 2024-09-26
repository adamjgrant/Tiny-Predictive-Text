import pickle
import os
import gc
import shutil
from tqdm import tqdm
import signal
import datasets
import logging
import sys
import asyncio
from lib.process_predictive_words import main as process_predictive_words
from lib.process_context_words import main as process_context_words
from lib.finish_filing import main as finish_filing
from lib.create_dictionary import create_batch
from lib.merge_batches import main as merge_batches
from lib.constants import PRUNE_FREQUENCY, TARGET_DICTIONARY_COUNT, TOTAL_WORD_COUNT
import argparse  # Import argparse for command-line parsing

# Global flag for graceful exit
interrupted = False

def signal_handler(sig, frame):
    global interrupted
    interrupted = True
    print("Graceful exit request received.")

# Signal handler for graceful exit
signal.signal(signal.SIGINT, signal_handler)

DEFAULT_TREE_STORE = {}

async def load_progress(progress_file):
    """Try to load progress using the new method (state_dict) or fall back to the old method."""
    if os.path.exists(progress_file):
        try:
            # Try to load the progress as a pickle object (new method)
            with open(progress_file, 'rb') as f:
                state_dict, word_count = pickle.load(f)
            print(f"Loaded progress using state_dict with word count {word_count}")
            return state_dict, word_count
        except (pickle.UnpicklingError, EOFError):
            # Fallback to the old method if pickle loading fails (old method)
            with open(progress_file, 'r') as f:
                start_position_str, word_length_str = f.read().strip().split(',')
                start_position = int(start_position_str)
                word_count = int(word_length_str)
            print(f"Loaded progress using old method from position {start_position} with word count {word_count}")
            return start_position, word_count
    return None, 0  # No progress file found

async def save_position(progress_file, dataset, word_count, tree_store):
    """Always save progress using the new state_dict method."""
    # Always create the state_dict, even if resuming from an old format
    state_dict = dataset.state_dict()
    with open(progress_file, 'wb') as f:
        pickle.dump((state_dict, word_count), f)
    print(f"Saved state_dict and word count {word_count}")
    await create_batch(tree_store, TARGET_DICTIONARY_COUNT)

    return DEFAULT_TREE_STORE

async def main(retain=False):
    tree_store = DEFAULT_TREE_STORE
    training_path = 'training'

    # Clear previous training data if not retaining
    if not retain and os.path.exists(training_path):
        shutil.rmtree(training_path)
        print("Previous training data cleared.")

    os.makedirs(training_path, exist_ok=True)

    # Load dataset from Hugging Face datasets
    datasets.logging.set_verbosity(datasets.logging.WARNING)
    logging.getLogger('fsspec').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    dataset = datasets.load_dataset('oscar-corpus/OSCAR-2201', language='en', split='train', streaming=True, trust_remote_code=True)

    word_count = 0
    start_position = 0
    state_dict = None

    # Load previous progress (either old or new format)
    if retain:
        state_dict, word_count = await load_progress('training/processing_progress.txt')
        if isinstance(state_dict, dict):
            dataset.load_state_dict(state_dict)
        else:
            # Resume using old method; we still skip to start position but will save with state_dict
            start_position = state_dict if isinstance(state_dict, int) else 0

    # Initialize progress bar
    pbar = tqdm(total=TOTAL_WORD_COUNT, unit='word', desc="Processing dataset", position=1)
    pbar.update(word_count)

    # Processing dataset
    for i, entry in enumerate(dataset.skip(start_position)):
        if interrupted:
            print("Script will terminate when done.")
            sys.exit(0)

        # Extract text and process words
        text = entry['text']
        words = text.split()

        # Update the progress bar with the number of words processed
        pbar.update(len(words))

        # Replace reserved characters
        words = [word.replace("score", "\sscore") for word in words]
        words = [word.replace("prediction", "\sprediction") for word in words]

        # Process words three at a time with a shifting window
        for j in range(len(words) - 2):
            word_count += 1

            # Get context and predictive words
            context_words = process_context_words(words, j)
            predictive_words = process_predictive_words(words, j)

            if not predictive_words:
                continue

            # File the words
            tree_store = finish_filing(tree_store, context_words, predictive_words)

            # Save position and prune periodically
            if (word_count + 1) % PRUNE_FREQUENCY == 0:
                tree_store = await save_position('training/processing_progress.txt', dataset, word_count, tree_store)
                gc.collect()

            # Silencing for now. Creating too many problems.
            # Merge batches periodically
            # if (word_count + 1) % (PRUNE_FREQUENCY * 25) == 0:
                # await merge_batches()

    # Final batch creation after processing is complete
    await create_batch(tree_store, TARGET_DICTIONARY_COUNT)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Training script with position retain functionality.')
    parser.add_argument('--retain', action='store_true', help='Retain and resume from last saved position.')
    args = parser.parse_args()

    asyncio.run(main(retain=args.retain))