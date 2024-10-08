import os
import shutil
import pickle
import threading
from .constants import TARGET_DICTIONARY_COUNT, MAX_PREDICTIONS, SUBBRANCH_PRUNE_SIZE
from .create_dictionary import create_dictionary_and_tokenize
import asyncio
# PRUNE_FREQUENCY = 4 * 1000 * 1000 # Every this many words
# TARGET_DICTIONARY_COUNT = 100

# # Total number of words in the dataset acc to https://huggingface.co/datasets/oscar-corpus/OSCAR-2201
# TOTAL_WORD_COUNT = 377376402775  

# SUBBRANCH_PRUNE_SIZE = 20
# MAX_PREDICTIONS = 3

# Ensure the directories exist
os.makedirs('training/merged_batches', exist_ok=True)
os.makedirs('training/processed_batches', exist_ok=True)
os.makedirs('backup', exist_ok=True)

def merge_dicts(dict1, dict2):
    """
    Recursively merges dict2 into dict1, handling the special case for predictions.
    """
    for key in dict2:
        if key in dict1:
            if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                merge_dicts(dict1[key], dict2[key])
            elif key == "predictions" and dict1[key] == dict2[key]:
                # If they have the same predictions, increase the score.
                dict1["score"] += 1  # Assuming each node with predictions has a score.
        else:
            dict1[key] = dict2[key]

def increase_scores(node):
    """
    Recursively increase scores in a tree node
    """
    if "score" in node:
        node["score"] += 1
    for key, value in node.items():
        if isinstance(value, dict):
            increase_scores(value)

def merge_predictions(tree1, tree2):
    """
    Merge two lists of predictions, increasing scores for duplicate predictions.
    """
    # Create a dict to store the merged predictions
    merged_predictions = {}
    for prediction in tree1 + tree2:
        # Get the prediction string
        prediction_str = ' '.join(prediction['prediction'])
        # If the prediction is already in the merged dict, increase the score
        if prediction_str in merged_predictions:
            merged_predictions[prediction_str]['score'] += 1
        else:
            merged_predictions[prediction_str] = prediction

    # Sort the merged predictions by score
    sorted_predictions = sorted(merged_predictions.values(), key=lambda x: x['score'], reverse=True)

    # Return only the top MAX_PREDICTIONS predictions
    return sorted_predictions[:MAX_PREDICTIONS]

def merge(tree1, tree2):
    """
    Merge two prediction trees, increasing scores for duplicate predictions.
    """
    # Base case: If either tree is not a dict, return the non-dict or merge lists directly
    if not isinstance(tree1, dict) or not isinstance(tree2, dict):
        return tree2

    # Initialize a new tree to hold the merge result
    merged_tree = {}

    # Get all unique keys from both trees
    all_keys = set(tree1.keys()) | set(tree2.keys())

    for key in all_keys:
        if key in tree1 and key in tree2:
            # If the key is in both trees, merge deeper
            merged_tree[key] = merge(tree1[key], tree2[key])
            
            # If tree1 is a dict
            if isinstance(tree1[key], dict):
                merged_tree[key]['score'] = tree1[key].get('score', 0) + tree2[key].get('score', 0)

            elif key == 'predictions':
              merged_tree[key] = merge_predictions(tree1[key], tree2[key])

        elif key in tree1:
            # If the key is only in the first tree, copy it
            if isinstance(tree1[key], dict):
              merged_tree[key] = tree1.get(key, {})
            else:
              merged_tree[key] = tree1[key]
        else:
            # If the key is only in the second tree, copy it
            if isinstance(tree2[key], dict):
              merged_tree[key] = tree2.get(key, {})
            else:
              merged_tree[key] = tree2[key]

    return merged_tree
  
def prune(merged_content, target_dict_size=TARGET_DICTIONARY_COUNT):
    def sort_keys_by_score(tree):
          # Sorts the tree's top-level keys based on their child score "score", highest first
          # Keeps the "score" key intact
          sorted_items = sorted(
              [(k, v) for k, v in tree.items() if k != "score" and isinstance(v, dict)],
              key=lambda item: item[1]["score"] if "score" in item[1] else 0, reverse=True
          )
          sorted_tree = {"score": tree.get("score", 0)} if "score" in tree else {}  # Preserve "score" score if it exists
          sorted_tree.update(dict(sorted_items))
          return sorted_tree

    def prune_top_level_entries_by_limit(tree, target_dict_size):
          pruned_tree = tree
          keys_to_delete = list(tree.keys())[target_dict_size:]
          for key in keys_to_delete:
              pruned_tree.pop(key)
          return pruned_tree

    top_sorted_tree = sort_keys_by_score(merged_content)
    top_pruned_tree = prune_top_level_entries_by_limit(top_sorted_tree, target_dict_size)

    def prune_and_sort_lower_branches(subtree, limit):
        if isinstance(subtree, dict):
            # Directly check for existence rather than getting a False default
            score_present = "score" in subtree  # Check if 'score' key exists
            predictions = subtree.get("predictions", False)  # Preserve predictions, if any
            
            # Filter out the special keys for sorting and pruning operations
            filtered_subtree = {k: v for k, v in subtree.items() if k not in ["score", "predictions"]}
            
            top_sorted_subtree = sort_keys_by_score(filtered_subtree)
            pruned_subtree = prune_top_level_entries_by_limit(top_sorted_subtree, limit)
            
            # Re-insert the 'score' if it was originally present, using a more reliable check
            if score_present:
                pruned_subtree["score"] = subtree["score"]  # Directly use the value from original subtree
            
            if predictions:  
              sorted_predictions = sorted(predictions, key=lambda x: x['score'], reverse=True)[:MAX_PREDICTIONS]
              pruned_subtree["predictions"] = sorted_predictions

            # Recursively process each child, skipping special keys
            for k, v in list(pruned_subtree.items()):
                if k not in ["score", "predictions"] and isinstance(v, dict):
                    pruned_subtree[k] = prune_and_sort_lower_branches(v, SUBBRANCH_PRUNE_SIZE)
                    
            return pruned_subtree
        else:
            return subtree

    for k in list(top_pruned_tree.keys()):
        if k != "score":
            subtree = top_pruned_tree[k]
            top_pruned_tree[k] = prune_and_sort_lower_branches(subtree, SUBBRANCH_PRUNE_SIZE)

    return top_pruned_tree 

def perform_file_operation(src, dst, operation='move'):
    try:
        if operation == 'move':
            shutil.move(src, dst)
        elif operation == 'copy':
            shutil.copy2(src, dst)
        print(f"Operation {operation} completed for: {src} to {dst}")
    except Exception as e:
        print(f"Error performing {operation} from {src} to {dst}: {e}")

def merge_and_prune_files(files, threads):
    file1_path = f'training/batches_to_process/{files[0]}'
    file2_path = f'training/batches_to_process/{files[1]}'

    # Get the contents of each file
    try:
        with open(file1_path, 'rb') as f1, open(file2_path, 'rb') as f2:
            content1 = pickle.load(f1)
            content2 = pickle.load(f2)
    except pickle.UnpicklingError as e:
        print(f"Error unpickling the files: {e}")
        thread6 = threading.Thread(target=perform_file_operation, args=(file1_path, f'training/processed_batches/{os.path.basename(file1_path)}', 'move'))
        thread7 = threading.Thread(target=perform_file_operation, args=(file2_path, f'training/processed_batches/{os.path.basename(file2_path)}', 'move'))
        threads.append(thread6)
        threads.append(thread7)
        thread6.start()
        thread7.start()
        for thread in threads:
          thread.join()
        return merge_and_prune_files(files[2:], threads)

    # Merge and prune
    merged_content = merge(content1, content2)
    pruned_content = prune(merged_content)

    # Save the result in training/merged_batches
    merged_filename = os.path.basename(file1_path).replace('.pkl', '') + '_merged.pkl'
    with open(f'training/merged_batches/{merged_filename}', 'wb') as f:
        pickle.dump(pruned_content, f)

    # Move the two files into training/processed_batches
    thread1 = threading.Thread(target=perform_file_operation, args=(file1_path, f'training/processed_batches/{os.path.basename(file1_path)}', 'move'))
    thread2 = threading.Thread(target=perform_file_operation, args=(file2_path, f'training/processed_batches/{os.path.basename(file2_path)}', 'move'))
    threads.append(thread1)
    threads.append(thread2)
    thread1.start()
    thread2.start()
    for thread in threads:
      thread.join()
    print(f'Merged and pruned {file1_path} and {file2_path} into {merged_filename}.')

    # Remove the first two items from the files variable
    remaining_files = files[2:]

    if not remaining_files:
        # Move everything from merged to batches if no more files are left in batches 
        for file in os.listdir('training/merged_batches'):
            thread3 = threading.Thread(target=perform_file_operation, args=(f'training/merged_batches/{file}', f'training/batches_to_process/{file}', 'move'))
            threads.append(thread3)
            thread3.start()
            thread3.join()

        batches_files = sorted(os.listdir('training/batches_to_process'))
        if len(batches_files) > 1:
            merge_and_prune_files(batches_files, threads)
        else:
            return
          
    else:
        # If there are more batches, run again with the next two files
        if len(remaining_files) > 1:
            # Remove the first two items from the files variable
            merge_and_prune_files(remaining_files, threads)

        if len(remaining_files) == 1:
            # If there is only one file, move it to merged_batches
            thread4 = threading.Thread(target=perform_file_operation, args=(f'training/batches_to_process/{remaining_files[0]}', f'training/merged_batches/{remaining_files[0]}', 'move'))
            threads.append(thread4)
            thread4.start()

            for file in os.listdir('training/merged_batches'):
                thread5 = threading.Thread(target=perform_file_operation, args=(f'training/merged_batches/{file}', f'training/batches_to_process/{file}', 'move'))
                threads.append(thread5)
                thread5.start()
            batches_files = sorted(os.listdir('training/batches_to_process'))

            for thread in threads:
                thread.join()

            if len(batches_files) > 1:
                merge_and_prune_files(batches_files, threads)
            else:
                return

def finish_merge():
    batches_files = sorted(os.listdir('training/batches_to_process'))
    if len(batches_files) > 1:
        threads = []
        merge_and_prune_files(batches_files, threads)
        for thread in threads:
            thread.join()
        finish_merge()
        
    print(f"Length of batches: {len(batches_files)}")

    # Copy the batch file to backup just in case.
    shutil.copy(f'training/batches_to_process/{batches_files[0]}', 'backup/dictionary.pkl')
    shutil.copy(f'training/processing_progress.txt', 'backup/processing_progress.txt')

    # Rename the first batch file to dictionary.pkl
    shutil.move(f'training/batches_to_process/{batches_files[0]}', 'training/dictionary.pkl')

    create_dictionary_and_tokenize() 

    # Delete all files in training/processed_batches
    shutil.rmtree('training/processed_batches', ignore_errors=True)
    shutil.rmtree('training/copy_of_batches_being_processed_in_this_round', ignore_errors=True)
    shutil.copy('training/dictionary.pkl', 'training/batches')

async def main():
    # If training/batches has more than one file, run the function with the first two files
    os.makedirs('training/copy_of_batches_being_processed_in_this_round', exist_ok=True)
    shutil.rmtree('training/batches_to_process', ignore_errors=True)
    os.makedirs('training/batches_to_process', exist_ok=True)
    threads = []

    for file in os.listdir('training/batches'):
        thread = threading.Thread(target=perform_file_operation, args=(f'training/batches/{file}', f'training/copy_of_batches_being_processed_in_this_round/{file}', 'move'))
        threads.append(thread)
        thread.start()

    for file in os.listdir('training/copy_of_batches_being_processed_in_this_round'):
        thread = threading.Thread(target=perform_file_operation, args=(f'training/copy_of_batches_being_processed_in_this_round/{file}', f'training/batches_to_process/{file}', 'copy'))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    batches_files = sorted(os.listdir('training/batches_to_process'))

    if len(batches_files) > 1:
        threads = []
        merge_and_prune_files(batches_files, threads)
        for thread in threads:
            thread.join()
        finish_merge()
    elif len(batches_files) == 1:
        finish_merge()

if __name__ == "__main__":
    asyncio.run(main())
