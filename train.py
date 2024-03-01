# Import necessary modules
import os
import sys
import pickle
import re
from collections import defaultdict
import csv
import shutil

# Define a function to slugify context words into a filename-safe string
def slugify(text):
    # Trim leading and trailing whitespace
    text = text.strip()
    # Replace all non-alphanumeric characters (except spaces) with nothing
    text = re.sub(r'[^\w\s]', '', text)
    # Replace all spaces with a single underscore
    text = re.sub(r'\s+', '_', text)
    # Convert to lowercase
    return text.lower()

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
  os.makedirs('training/dictionaries', exist_ok=True)
  scores_file_path = 'training/scores.pkl'
  if not os.path.exists(scores_file_path):
      with open(scores_file_path, 'wb') as scores_file:
          pickle.dump({}, scores_file, protocol=pickle.HIGHEST_PROTOCOL)

  # Read the CSV file and process the training data
  # Open the CSV file
  with open(training_data_file, 'r', newline='', encoding='utf-8') as csvfile:
      reader = csv.reader(csvfile)
      for row in reader:
          words = ' '.join(row).split()
          # Process words three at a time with shifting window
          for i in range(len(words) - 2):
              context_words = words[i:i+3]
              predictive_words = []
              # Determine predictive words, up to three or until a punctuation mark
              for j in range(i + 3, min(i + 6, len(words))):
                  if words[j] in ['.', ',', '\n', '\r', '\r\n']:
                      break
                  predictive_words.append(words[j])
              if not predictive_words:  # Skip if there are no predictive words
                  continue
              
              # Slugify the context words
              context_slug = slugify('_'.join(context_words))
              
              # Load or initialize the trie for the context words from its .pkl file
              trie_file_path = os.path.join('training/dictionaries', f'{context_slug}.pkl')
              trie = load_trie(trie_file_path)
              
              # Update the trie with the predictive words
              update_trie(trie, predictive_words)
              
              # Save the updated trie back to the .pkl file
              save_trie(trie, trie_file_path)
              
              # Update the counts in scores.pkl for the context words slug
              update_scores(scores_file_path, context_slug)

# Check if the script is being run directly and call the main function
if __name__ == "__main__":
    main()