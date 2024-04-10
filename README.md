# Tiny-Predictive-Text
A demonstration of predictive text without an LLM, using permy.link

[Check it out](https://adamgrant.info/tiny-predictive-text)

## Quickstart

Add Tiny predict to your HTML.

```html
  <script src="tiny-predict.min.js"></script>
  <script>
    import { Predict, PredictionState } from "tiny-predict.min.js";
    // Rest of code
  </script>
</body>
```

To generate a suggestion, send in the string as an input parameter

```javascript
const prediction = new Predict({
  input: "I would love to"
});
prediction.addEventListener("update", (suggestion, state) => {
  // suggestion;        // Suggestion as string
  // suggestion.next; // Get a new suggestion as string
  // if (state == "INSIDE_SUGGESTION") {
  //   suggestion.components // Array of matching versus not-yet-matched suggestion string
  // }
})
```

The event listener will provide the first best suggestion. 

The user may end up typing characters that better fit other predictions

**Work in progress...**

## Training

No GPUs OS requirements or nVidia libraries needed. I run this on my Macbook Pro with the included version of Python.

- `pip install .`
- `huggingface-cli login`

then 

`python train.py --retain`

To begin the training. Every once in a while it will optimize by pruning word set dictionaries and branches recursively. At this point (look for it in the logs) it will create a new batch file in /training/batches. It does this so the script can be restarted and it can pick up where it left off. Making separate batches also prevents the script from locking up.

### Merging batches

Once enough batches are created, merge them with

`python -m lib.merge_batches`

This will take two batches at a time, merging them into one in training/merged_batches. It will then move the originals into training/processed_batches.

After it has gone through and merged couples, it will put all the merged batches back into training/batches and continue this process again until it is left with only one single merged batch.

### Creating the dictionary

With the single merged batch, it's time to optimize this further and get it ready for the web environment by converting it to msgpack.

`python -m lib.create_dictionary`

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

```
make
```

Or

```
npx webpack
```

and

```bash
wasm-pack build --target web wasm
```

# Testing

Test the Rust code with:
`cargo test --manifest-path wasm/Cargo.toml`

Test the python code with:
`python -m unittest test.py`