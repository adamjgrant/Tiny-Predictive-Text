import os
import shutil
import pickle

# Ensure the directories exist
os.makedirs('training/merged_epochs', exist_ok=True)
os.makedirs('training/processed_epochs', exist_ok=True)

def merge(content1, content2):
  return # TODO

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

    # Save the result in training/merged_epochs
    merged_filename = os.path.basename(file1_path).replace('.pkl', '') + '_merged.pkl'
    with open(f'training/merged_epochs/{merged_filename}', 'wb') as f:
        pickle.dump(pruned_content, f)

    # Move the two files into training/processed_epochs
    shutil.move(file1_path, f'training/processed_epochs/{os.path.basename(file1_path)}')
    shutil.move(file2_path, f'training/processed_epochs/{os.path.basename(file2_path)}')

    # Check for remaining files and act accordingly
    remaining_files = os.listdir('training/epochs')
    if not remaining_files:
        # Move everything from merged to epochs if no more files are left in epochs
        for file in os.listdir('training/merged_epochs'):
            shutil.move(f'training/merged_epochs/{file}', f'training/epochs/{file}')
    else:
        # If there are more epochs, run again with the next two files
        if len(remaining_files) > 1:
            merge_and_prune_files('training/epochs/' + remaining_files[0], 'training/epochs/' + remaining_files[1])

# If training/epochs has more than one file, run the function with the first two files
epochs_files = sorted(os.listdir('training/epochs'))
if len(epochs_files) > 1:
    merge_and_prune_files(f'training/epochs/{epochs_files[0]}', f'training/epochs/{epochs_files[1]}')
elif len(epochs_files) == 1:
    # If there is only one file, move it to processed and make a copy in merged
    single_file_path = f'training/epochs/{epochs_files[0]}'
    shutil.move(single_file_path, f'training/processed_epochs/{epochs_files[0]}')
    shutil.copy(f'training/processed_epochs/{epochs_files[0]}', 'training/merged_epochs/merged_epoch.pkl')
