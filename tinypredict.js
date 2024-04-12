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

    const apply_ambition_penalties = (suggestions) => {
      const quality = suggestions.quality;
      let predictions = suggestions.prediction;
      predictions = predictions.map((prediction) => {
        let penalty;
        const prediction_length = prediction.split(" ").length;
        if (prediction_length === 1) penalty = 5;
        if (prediction_length === 2) penalty = -1;
        if (prediction_length === 3) penalty = -5;

        return {
          "completion": prediction,
          "quality": quality + (quality > 0 ? penalty : 0)
        }
      });
      predictions = predictions.sort((a, b) => b.quality - a.quality);
      suggestions.prediction = predictions;
      return suggestions;
    }

    window.getPredictiveText = async function(inputText) {
      try {
          let suggestions = await get_predictive_text(inputText);
          suggestions = apply_ambition_penalties(suggestions);
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