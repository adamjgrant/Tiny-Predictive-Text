# Import necessary modules
import os
import sys
import shutil
from tqdm import tqdm
from slugify import slugify
import string
from create_fingerprint_dictionary import main as flatten_to_dictionary
import signal
import pickle

PRUNE_FREQUENCY = 10 * 1000 * 1000 # Every this many document positions
CHUNK_SIZE = 1024 # 1KB per chunk
TARGET_DICTIONARY_COUNT = 25 * 1000
CONTEXT_WORD_LENGTH = 10
MEASUREMENT_DECIMAL_PLACES = 4

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
    with open('training/trie_fingerprint_store.pkl', 'wb') as f:
        pickle.dump(trie_store, f, protocol=pickle.HIGHEST_PROTOCOL)
    print("trie_fingerprint_store saved due to interruption.")

DEFAULT_TRIE_STORE ={ "fingerprints": {}, "scores": {}} 

def load_trie_store():
    # (Scores)
    # {
    #   "what_i_mean": 12, ...      (Number of times we found it)
    # }
    try:
        with open('training/trie_fingerprint_store.pkl', 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return DEFAULT_TRIE_STORE

# Define a function to slugify context words into a filename-safe string
def _slugify(text):
    return slugify(text, separator="_")

def vowel_to_consonant_ratio(phrase, existing_vcr, instances):
    vowels = "aeiouAEIOU"
    consonants = "bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ"
    vowel_count = sum(1 for char in phrase if char in vowels)
    consonant_count = sum(1 for char in phrase if char in consonants)
    new_vcr = vowel_count / max(1, consonant_count)  # Avoid division by zero
    
    # Averaging with existing value
    if existing_vcr is not None:
        average_vcr = ((existing_vcr * (instances - 1)) + new_vcr) / instances
    else:
        average_vcr = new_vcr
    
    return round(average_vcr, MEASUREMENT_DECIMAL_PLACES)

def word_length_distribution(string, existing_wld, instances):
    words = string.split()
    # Initialize new distribution with the specific categories
    new_distribution = {'<=3': 0, '4': 0, '5': 0, '6': 0, '>=7': 0}
    
    # Count words falling into each category
    for word in words:
        length = len(word)
        if length <= 3:
            new_distribution['<=3'] += 1
        elif length == 4:
            new_distribution['4'] += 1
        elif length == 5:
            new_distribution['5'] += 1
        elif length == 6:
            new_distribution['6'] += 1
        else:  # length >= 7
            new_distribution['>=7'] += 1
    
    # Averaging with existing value
    if existing_wld is not None:
        # Update each category count by averaging
        for category, count in new_distribution.items():
            if category in existing_wld:
                existing_wld[category] = ((existing_wld[category] * (instances - 1)) + count) / instances
            else:
                existing_wld[category] = count / instances
            existing_wld[category] = round(existing_wld[category], MEASUREMENT_DECIMAL_PLACES)
        average_wld = existing_wld
    else:
        average_wld = {category: count / instances for category, count in new_distribution.items()}
    
    return average_wld

def unique_word_ratio(string, existing_uwr, instances):
    words = string.split()
    unique_words = len(set(words))
    total_words = len(words)
    new_uwr = unique_words / max(1, total_words)  # Avoid division by zero
    
    # Averaging with existing value
    if existing_uwr is not None:
        average_uwr = ((existing_uwr * (instances - 1)) + new_uwr) / instances
    else:
        average_uwr = new_uwr
    
    return round(average_uwr, MEASUREMENT_DECIMAL_PLACES)

# Define a function to load or initialize the trie from memory
def load_trie(trie_store, predictive_slug):
    # Access the trie data by first navigating to the path, then the context_slug
    return trie_store["fingerprints"].get(predictive_slug, {})

# Process the values for the trie
def process_trie(trie, actual_phrase, completion, anchor_word):
  # Look at the incoming trie. If it has existing values we should process them
  # with the ones we compute on the incoming context words. (Avg over inst)
  # Design:
  # (Fingerprints)
  # {
  #   "what_i_mean": {
  #     "completion": "what I mean",  (Everything below is about the 10* words found before this)
  #     "vcr": 0.72,              (Vowel to consonant ratio)
  #     "wld": [4,2,3,1],         (Word length distribution, 3-, 4-, 5- and >5- length)
  #     "uwr": 0.98,              (Unique word ratio) 
  #     "inst": 4,                (Number of instances found)
  #     "anc": ["is"]             (Words found just before this one)
  #   },
  # }
  #
  # *On average, an English sentence is 15-20 words long, so 13 (10+3) length is reasonable.
  instances = trie.get("inst", 0) + 1

  # Retrieve the "anc" dictionary, default to an empty dict if not found
  anc = trie.get("anc", {})

  # Increment the score for the anchor word, or initialize it to 1 if it doesn't exist
  anc[anchor_word] = anc.get(anchor_word, 0) + 1

  # Sort the anc dictionary by score in descending order and keep the top 10 items
  sorted_anc = dict(sorted(anc.items(), key=lambda item: item[1], reverse=True)[:10])

  # Update the trie with the new information
  trie.update({
      "completion": completion,
      "vcr": vowel_to_consonant_ratio(actual_phrase, trie.get("vcr", None), instances),
      "wld": word_length_distribution(actual_phrase, trie.get("wld", None), instances),
      "uwr": unique_word_ratio(actual_phrase, trie.get("uwr", None), instances),
      "inst": instances,
      "anc": sorted_anc  # Update the sorted anc dictionary back to trie
  })


def save_trie(trie_store, trie, predictive_slug):
    # Assign the trie to the specified path and context_slug
    trie_store["fingerprints"][predictive_slug] = trie

def update_scores(trie_store, predictive_slug):
    if predictive_slug not in trie_store['scores']:
        trie_store['scores'][predictive_slug] = 0
    trie_store['scores'][predictive_slug] += 1

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
        print("Usage: python train-fingerprints.py <name of training data>.txt")
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
  progress_file = 'training/processing_fingerprints_progress.txt'

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

              # Process words with a context window of ten words at a time
              for i in range(len(words) - (CONTEXT_WORD_LENGTH - 1)):  # Adjust based on CONTEXT_WORD_LENGTH
                  context_words = words[i:i + CONTEXT_WORD_LENGTH]  # Use CONTEXT_WORD_LENGTH for context window
                  predictive_words = []
                  anchor_word = slugify(context_words[-1])

                  # Determine predictive words, starting right after the context window, up to three words
                  for j in range(i + CONTEXT_WORD_LENGTH, min(i + CONTEXT_WORD_LENGTH + 3, len(words))):
                      word = words[j]
                      # Define and use punctuation sets as before
                      internal_punctuation = {"'", "-"}
                      additional_punctuation = {"“", "”", "–", "—"}
                      ending_punctuation = (set(string.punctuation) | additional_punctuation) - internal_punctuation
                      
                      # Process each word for ending punctuation and collect predictive words as before
                      cleaned_word = ''.join(char for char in word if char not in ending_punctuation)
                      if cleaned_word != word or any(char in ending_punctuation for char in word):
                          predictive_words.append(cleaned_word)
                          break
                      else:
                          predictive_words.append(cleaned_word)

                  if not predictive_words:
                      continue
                    
                  finish_filing(trie_store, context_words, predictive_words, anchor_word)

  flatten_to_dictionary(trie_store, TARGET_DICTIONARY_COUNT) 

def finish_filing(trie_store, context_words, predictive_words, anchor_word):
    # Slugify the context words
    completion = " ".join(predictive_words)
    predictive_slug = _slugify(completion)
    actual_phrase = " ".join(context_words)

    # Get or create the dict entry for this predictive slug
    trie = load_trie(trie_store, predictive_slug)
    
    # With that entry, start processing the properties of the context words
    process_trie(trie, actual_phrase, completion, anchor_word)
    
    # Save the updated trie back to the .pkl file
    save_trie(trie_store, trie, predictive_slug)
    
    # Update the counts in scores_3_words.pkl for the context words slug
    update_scores(trie_store, predictive_slug) 

# Check if the script is being run directly and call the main function
if __name__ == "__main__":
    main()