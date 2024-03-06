import string

def main(words):
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
      return [ cleaned_word, True ]
  else:
      return [ cleaned_word, False ]
