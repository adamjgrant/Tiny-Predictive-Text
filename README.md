# Tiny-Predictive-Text
A demonstration of predictive text without an LLM, using permy.link

[Check it out](https://adamgrant.info/tiny-predictive-text)

## Quickstart

1. Include all of the files in [the /dist directory](https://github.com/adamjgrant/Tiny-Predictive-Text/tree/main/dist) as well as [dictionary.msgpack](https://github.com/adamjgrant/Tiny-Predictive-Text/blob/main/dictionary.msgpack) and [tokens.msgpack](https://github.com/adamjgrant/Tiny-Predictive-Text/blob/main/tokens.msgpack) in the root of your project.

2. Add Tiny predict to your HTML.

```html
<script type="module" src="tinypredict.js"></script>
```

3. Interace with the library

``` 
<script>
  window.addEventListener('tinypredict-ready', () => {
    const input = "I would like to";

    window.getPredictiveText(input).then(suggestions => {
      // Use the suggestions object here.
    });
  });
</script>
```

### Suggestions Object

Example suggestions object. The part you'll probably want to use most is `prediction` which gives you one or more
suggested completions in order of quality.

```json
{
  "anchor": "you", 
  "anchor_token": 206, 
  "first_level_context": "rnh", 
  "second_level_context": "wt", 
  "quality": 16, 
  "prediction": ["can never get", "always start with", "will cancel existing"]
}
```

More context on what this object means can be [found here](https://www.adamgrant.info/tiny-predictive-text)

### Quality scoring

(See suggestions object above)

While not perfect, the quality score is a rough estimate from 0-100 of how likely the prediction is to be correct. The higher the number, the more likely it is to be correct.

This can be useful if you want your predictions to be less noisy and only show up if a significant threshold of quality has been met.

## Training

No GPUs OS requirements or nVidia libraries needed. I run this on my Macbook Pro with the included version of Python.

- `pip install .`
- `huggingface-cli login`

then 

`python train.py --retain`

To begin the training. Every once in a while it will optimize by pruning word set dictionaries and branches recursively. At this point (look for it in the logs) it will create a new batch file in /training/batches. It does this so the script can be restarted and it can pick up where it left off. Making separate batches also prevents the script from locking up.

### Creating the dictionary

The following can be performed at any time, including when the training script is still running. 
This is useful for just taking a peek at the data so far and playing with it in the web interface.

Once enough batches are created, merge them with

`python -m lib.merge_batches`

This will merge all the batches and create a msgpack dictionary once all merges have completed.

## WASM Development

### Installation

Install Rust

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Install wasm-pack

```bash
cargo install wasm-pack
```

Install npm dependencies

```
npm install
```

Create webpack

```bash
wasm-pack build --target web wasm && npx webpack
```

# Testing

Test the Rust code with:
`cargo test --manifest-path wasm/Cargo.toml`

Test the python code with:
`python -m unittest test.py`