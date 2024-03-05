# Tiny-Predictive-Text
A demonstration of predictive text without an LLM, using permy.link

[Check it out](https://adamgrant.info/tiny-predictive-text)

## Usage
In script.js uncomment only the dictionary size you want to use. The larger the dictionary, the larger the file and will impact load times.

```javascript
import { dictionary } from './dictionary-10K.js';
// import { dictionary } from './dictionary-25K.js';
// import { dictionary } from './dictionary-100K.js';
// import { dictionary } from './dictionary-250K.js';
```

## Training

No GPUs OS requirements or nVidia libraries needed. I run this on my Macbook Pro with the included version of Python.

- `pip install tqdm`
- `pip install python-slugify`
- [Download training data](https://cdn.everything.io/datasets/blogs-news-twitter.txt.zip)
- Save it in the root as `train.txt`.
- Run the training with `python train.py train.txt`. Every once in a while it will optimize by pruning word set dictionaries and branches recursively. At this point (look for it in the logs) it will create the dictionary.js file the demo needs to run. Let it keep running and it will continuously improve that dictionary as it continues its training.

🪄 Tip: Run it again anytime with the `--retain` flag to pick up where you left off.
You can hit ctrl+C to gracefully exit the training. It will try to finish what it was doing before exiting so as not to corrupt any files on the next run.