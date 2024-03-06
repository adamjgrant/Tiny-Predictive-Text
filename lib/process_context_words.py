PREPOSITIONS = ["and", "or", "but", "if", "of", "at", "by", "for", "with", "to", "in", "on"] 
TO_BE = ["am", "is", "are", "was", "were", "be", "been", "being"]
TO_HAVE = ["have", "has", "had", "having"]
ARTICLES = ["the", "a", "an"]

def get_acronym_for_words(words):
    # Get the first letter of each word and convert to uppercase to form the acronym
    return ''.join(word[0].upper() for word in words if word)

def remove_extra_words(words):
    # Define a list of words to remove
    extra_words = set(PREPOSITIONS + TO_BE + TO_HAVE + ARTICLES)
    # Return a list of words not in the extra_words set
    return [word for word in words if word.lower() not in extra_words]

def main(words, index):
    # Assuming words is a list of strings and index is the index to find the anchor
    anchor = words[index] if index < len(words) else ""

    # Adjust the windows relative to the given index
    # Use up to three words before the second part as the first part
    first_part_start = max(0, index - 6)  # Ensure start index is not negative
    first_part_end = max(0, index - 3)
    first_part_words = words[first_part_start:first_part_end]
    first_part = get_acronym_for_words(remove_extra_words(first_part_words))

    # Second part: Use the three words immediately before the anchor word
    second_part_start = max(0, index - 3)  # Ensure start index is not negative
    second_part_words = words[second_part_start:index]
    second_part = get_acronym_for_words(second_part_words)

    return {
        "anchor": anchor,
        "context_window": [first_part, second_part]
    }