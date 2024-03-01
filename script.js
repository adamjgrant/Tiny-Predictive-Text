import { Tree } from './permute.js';
import { dictionary } from './dictionary.js';

let suggested_text_on_deck = "";
const [entry, suggestion] = [
  document.getElementById("entry"),
  document.getElementById("suggestion")
];

const get_word = () => {
  let last_word = entry.value.trim().split(" ");
  return last_word[last_word.length - 1].toLowerCase();
};

const clear_suggestion = () => {
  suggestion.innerHTML = "...";
  suggested_text_on_deck = "";
}

const get_suggestion = (word) => {
  word = word.replace(/[\s\:\.\,]/g, "");
  let new_tree = dictionary[word];
  if (!new_tree) return "";
  let permute = new Tree({ "main": new_tree[0][1] });
  return permute.one;
};

entry.addEventListener("keydown", (event) => {
  if (event.keyCode === 9) {
    event.preventDefault();
    const space = entry.value.split("").reverse()[0] === " " ? "" : " ";
    entry.value = entry.value + space + suggested_text_on_deck;
    clear_suggestion();
  }
});

entry.addEventListener("keyup", () => {
  const word = get_word();
  if (word === "") return clear_suggestion();
  console.log(word);
  const suggested_word = get_suggestion(word);
  if (!suggested_word) return clear_suggestion();
  suggested_text_on_deck = suggested_word;
  suggestion.innerHTML = suggested_word;
});
