import init, { load_dictionary, load_tokens, get_predictive_text } from './wasm/pkg/tinypredict.js';

async function run() {
    await init();

    // Fetch and load the dictionary.msgpack
    const dictionaryResponse = await fetch('./dictionary-test.msgpack');
    const dictionaryBuffer = await dictionaryResponse.arrayBuffer();
    const dictionary = load_dictionary(new Uint8Array(dictionaryBuffer));
    console.log(dictionary);

    // Similarly for tokens.msgpack
    const tokensResponse = await fetch('./tokens-test.msgpack');
    const tokensBuffer = await tokensResponse.arrayBuffer();
    const tokens = load_tokens(new Uint8Array(tokensBuffer));
    console.log(tokens);

    window.getPredictiveText = async function(inputText) {
      try {
          const suggestions = await get_predictive_text(inputText);
          console.log("Predictive text suggestions:", suggestions);
          return suggestions;
      } catch (error) {
          console.error("Error getting predictive text:", error);
          return [];
      }
    }

    // Dispatch a custom event to signal that the module is ready
    const event = new CustomEvent('tinypredict-ready', {
      detail: { getPredictiveText: window.getPredictiveText }
    });
    window.dispatchEvent(event);
}

run();