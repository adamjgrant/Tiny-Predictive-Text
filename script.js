import { Tree } from './permute.js';
import { dictionary } from './dictionary-5.4MB.js';
// import { dictionary } from './dictionary-11.9MB.js';
// import { dictionary } from './dictionary-33.7MB.js';

let suggested_text_on_deck = "";
const [entry, suggestion] = [
  document.getElementById("entry"),
  document.getElementById("suggestion")
];

const get_word = (word=entry.value) => {
  let last_three_words = word.trim().split(" ");
  return slugify(last_three_words.slice(-3), "_");
};

function slugify(text, separator) {
  text = text.toString().toLowerCase().trim()

  const sets = [
    { to: "a", from: "[ÀÁÂÃÅÆĀĂĄẠẢẤẦẨẪẬẮẰẲẴẶ]" },
    { to: "ae", from: "[ÄÆ]" },
    { to: "c", from: "[ÇĆĈČ]" },
    { to: "d", from: "[ÐĎĐÞ]" },
    { to: "e", from: "[ÈÉÊËĒĔĖĘĚẸẺẼẾỀỂỄỆ]" },
    { to: "g", from: "[ĜĞĢǴ]" },
    { to: "h", from: "[ĤḦ]" },
    { to: "i", from: "[ÌÍÎÏĨĪĮİỈỊ]" },
    { to: "j", from: "[Ĵ]" },
    { to: "ij", from: "[Ĳ]" },
    { to: "k", from: "[Ķ]" },
    { to: "l", from: "[ĹĻĽŁ]" },
    { to: "m", from: "[Ḿ]" },
    { to: "n", from: "[ÑŃŅŇ]" },
    { to: "o", from: "[ÒÓÔÕØŌŎŐỌỎỐỒỔỖỘỚỜỞỠỢǪǬƠ]" },
    { to: "oe", from: "[ŒÖØ]" },
    { to: "p", from: "[ṕ]" },
    { to: "r", from: "[ŔŖŘ]" },
    { to: "s", from: "[ŚŜŞŠ]" },
    { to: "ss", from: "[ß]" },
    { to: "t", from: "[ŢŤ]" },
    { to: "u", from: "[ÙÚÛŨŪŬŮŰŲỤỦỨỪỬỮỰƯ]" },
    { to: "ue", from: "[Ü]" },
    { to: "w", from: "[ẂŴẀẄ]" },
    { to: "x", from: "[ẍ]" },
    { to: "y", from: "[ÝŶŸỲỴỶỸ]" },
    { to: "z", from: "[ŹŻŽ]" },
    { to: "-", from: "[·/_,:;']" },
  ]

  sets.forEach((set) => {
    text = text.replace(new RegExp(set.from, "gi"), set.to)
  })

  text = text
    .toString()
    .toLowerCase()
    .replace(/\s+/g, "-") // Replace spaces with -
    .replace(/&/g, "-and-") // Replace & with 'and'
    .replace(/[^\w\-]+/g, "") // Remove all non-word chars
    .replace(/\--+/g, "-") // Replace multiple - with single -
    .replace(/^-+/, "") // Trim - from start of text
    .replace(/-+$/, "") // Trim - from end of text

  if (typeof separator !== "undefined" && separator !== "-") {
    text = text.replace(/-/g, separator)
  }

  return text
}

const clear_suggestion = () => {
  suggestion.innerHTML = "...";
  suggested_text_on_deck = "";
  suggestion.classList.remove("two_word");
  suggestion.classList.remove("three_word");
}

const get_suggestion = (word) => {
  let new_tree = dictionary[word];
  if (!new_tree) { 
    return ""; 
  }
  let permute = new Tree({ "main": new_tree });
  return permute.one;
};

const use_suggestion = (event=undefined) => {
  const space = entry.value.split("").reverse()[0] === " " ? "" : " ";
  entry.value = entry.value + space + suggested_text_on_deck;
  clear_suggestion();
}

entry.addEventListener("keydown", (event) => {
  if (event.keyCode === 9) {
    event.preventDefault();
    use_suggestion();
  }
});
suggestion.addEventListener("click", () => {
  use_suggestion();
  entry.focus();
  check_for_suggestion();
});

const set_suggested_word_class = (word_parts) => {
  suggestion.classList.remove("two_word");
  suggestion.classList.remove("three_word");
  if (word_parts.length > 2) return suggestion.classList.add("three_word");
  if (word_parts.length > 1) return suggestion.classList.add("two_word");
  return
}

const cut_after_punctuation = (word_parts, delimiter) => {
  let split_up = word_parts.join(" ").split(delimiter).pop().trim();
  return split_up.split(" ").filter(word => word);
}

const find_a_suggestion = (word_parts) => {
  let suggested_word;

  word_parts = cut_after_punctuation(word_parts, ".");
  word_parts = cut_after_punctuation(word_parts, ",");

  let word = get_word(word_parts.join(" "));
  suggested_word = get_suggestion(word);
  if (suggested_word !== "") {
    set_suggested_word_class(word_parts);
    return suggested_word
  }
  word_parts.shift();
  if (!word_parts.length) return false;
  return find_a_suggestion(word_parts)
}

const check_for_suggestion = () => {
  let word = get_word();
  if (word === "") return clear_suggestion();

  let suggested_word = find_a_suggestion(entry.value.trim().split(" ").slice(-3));

  if (!suggested_word) {
    return clear_suggestion();
  }
  suggested_text_on_deck = suggested_word;
  suggestion.innerHTML = suggested_word;
}

entry.addEventListener("keyup", check_for_suggestion);
