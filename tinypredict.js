import init, { load_dictionary, load_tokens, get_predictive_text } from './wasm/pkg/tinypredict.js';

async function run() {
    await init();

    // Fetch and load the dictionary.msgpack
    const dictionaryResponse = await fetch('./dictionary.msgpack');
    const dictionaryBuffer = await dictionaryResponse.arrayBuffer();
    load_dictionary(new Uint8Array(dictionaryBuffer));

    // Similarly for tokens.msgpack
    const tokensResponse = await fetch('./tokens.msgpack');
    const tokensBuffer = await tokensResponse.arrayBuffer();
    load_tokens(new Uint8Array(tokensBuffer));

    window.getPredictiveText = async function(inputText) {
      try {
          const suggestions = await get_predictive_text(inputText, 3);
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