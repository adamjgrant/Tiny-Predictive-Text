import string

def main(words, index):
  predictive_words = []
  # Determine predictive words, up to three or until one ends with a punctuation mark
  for j in range(index + 6, min(index + 9, len(words))):
    word = words[j]
    # Define a set of punctuation that is allowed within a word
    internal_punctuation = {"'", "-"}
    additional_punctuation = {"“", "”", "–", "—"}
    # Create a set of punctuation that signals the end of a word, excluding the internal punctuation
    ending_punctuation = (set(string.punctuation) | additional_punctuation) - internal_punctuation
    
    # Check for and remove ending punctuation from the word
    cleaned_word = ''.join(char for char in word if char not in ending_punctuation)
    
    # If after cleaning the word it ends with any ending punctuation, or if the original word contained ending punctuation
    if cleaned_word != word or any(char in ending_punctuation for char in word):
      predictive_words.append(cleaned_word)
      break
    else:
      predictive_words.append(cleaned_word)
      continue
  return predictive_words

                    

