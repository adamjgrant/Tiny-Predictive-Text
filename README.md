# Tiny-Predictive-Text
A demonstration of predictive text without an LLM, using permy.link

[Check it out](https://adamgrant.info/tiny-predictive-text)

## Training

No GPUs OS requirements or nVidia libraries needed. I run this on my Macbook Pro with the included version of Python.

- `pip install tqdm`
- `pip install python-slugify`
- [Download training data](https://cdn.everything.io/datasets/blogs-news-twitter.txt.zip)
- Save it in the root as `train.txt`.
- Run the training with `python train.py train.txt`. Every once in a while it will optimize by pruning word set dictionaries and branches recursively. At this point (look for it in the logs) it will create the dictionary.js file the demo needs to run. Let it keep running and it will continuously improve that dictionary as it continues its training.