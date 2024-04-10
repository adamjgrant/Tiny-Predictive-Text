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