import os
import shutil
import pickle

# Ensure the directories exist
os.makedirs('training/merged_batches', exist_ok=True)
os.makedirs('training/processed_batches', exist_ok=True)

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

        elif key in tree1:
            # If the key is only in the first tree, copy it
            merged_tree[key] = tree1[key]
        else:
            # If the key is only in the second tree, copy it
            merged_tree[key] = tree2[key]

    return merged_tree
  
def prune(content):
  return # TODO

def merge_and_prune_files(file1_path, file2_path):
    # Get the contents of each file
    with open(file1_path, 'rb') as f1, open(file2_path, 'rb') as f2:
        content1 = pickle.load(f1)
        content2 = pickle.load(f2)

    # Merge and prune
    merged_content = merge(content1, content2)  # Assuming merge is a defined function
    pruned_content = prune(merged_content)  # Assuming prune is a defined function

    # Save the result in training/merged_batches
    merged_filename = os.path.basename(file1_path).replace('.pkl', '') + '_merged.pkl'
    with open(f'training/merged_batches/{merged_filename}', 'wb') as f:
        pickle.dump(pruned_content, f)

    # Move the two files into training/processed_batches
    shutil.move(file1_path, f'training/processed_batches/{os.path.basename(file1_path)}')
    shutil.move(file2_path, f'training/processed_batches/{os.path.basename(file2_path)}')

    # Check for remaining files and act accordingly
    remaining_files = os.listdir('training/batches')
    if not remaining_files:
        # Move everything from merged to batches if no more files are left in batches 
        for file in os.listdir('training/merged_batches'):
            shutil.move(f'training/merged_batches/{file}', f'training/batches/{file}')
    else:
        # If there are more batches, run again with the next two files
        if len(remaining_files) > 1:
            merge_and_prune_files('training/batches/' + remaining_files[0], 'training/batches/' + remaining_files[1])

# # If training/batches has more than one file, run the function with the first two files
# batches_files = sorted(os.listdir('training/batches'))
# if len(batches_files) > 1:
#     merge_and_prune_files(f'training/batches/{batches_files[0]}', f'training/batches/{batches_files[1]}')
# elif len(batches_files) == 1:
#     # If there is only one file, move it to processed and make a copy in merged
#     single_file_path = f'training/batches/{batches_files[0]}'
#     shutil.move(single_file_path, f'training/processed_batches/{batches_files[0]}')
#     shutil.copy(f'training/processed_batches/{batches_files[0]}', 'training/merged_batches/merged_batch.pkl')