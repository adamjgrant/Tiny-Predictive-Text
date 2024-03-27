###########
# RECIPES #
###########
# 1.4MB: ? Target dictionary count ? Prune frequency
PRUNE_FREQUENCY = 4 * 1000 * 1000 # Every this many words
TARGET_DICTIONARY_COUNT = 100

# Total number of words in the dataset acc to https://huggingface.co/datasets/oscar-corpus/OSCAR-2201
TOTAL_WORD_COUNT = 377376402775  

SUBBRANCH_PRUNE_SIZE = 20
MAX_PREDICTIONS = 3