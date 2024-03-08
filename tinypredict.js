import init, { load_dictionary, load_tokens } from './wasm/pkg/tinypredict.js';

async function run() {
    await init();

    // Fetch and load the dictionary.msgpack
    const dictionaryResponse = await fetch('./dictionary.msgpack');
    const dictionaryBuffer = await dictionaryResponse.arrayBuffer();
    const dictionary = load_dictionary(new Uint8Array(dictionaryBuffer));
    console.log(dictionary);

    // Similarly for tokens.msgpack
    const tokensResponse = await fetch('./tokens.msgpack');
    const tokensBuffer = await tokensResponse.arrayBuffer();
    const tokens = load_tokens(new Uint8Array(tokensBuffer));
    console.log(tokens);
}

run();