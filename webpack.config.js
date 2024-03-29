const path = require('path');
const CopyPlugin = require('copy-webpack-plugin');

module.exports = {
  entry: './tinypredict.js', // Adjust this path to your entry point generated by wasm-pack
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'tinypredict.js', // Name of the bundled JS file
  },
  experiments: {
    asyncWebAssembly: true,
  },
  plugins: [
    new CopyPlugin({
      patterns: [
        { from: './wasm/pkg/tinypredict_bg.wasm', to: 'tinypredict_bg.wasm' }
      ],
    }),
  ],
  mode: 'production',
};