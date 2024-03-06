import { dictionary_anchors } from './dictionary-anchors.js';
import { dictionary_properties } from './dictionary-properties.js';
import { token_mapping as token_to_word } from './token-mapping.js';

const MED_SCORE_THRESHOLD = 6;
const HIGH_SCORE_THRESHOLD = 4;

const state_machine = {
  no_suggestion: ["has_suggestion"],
  has_suggestion: ["inside_suggestion", "no_suggestion"],
  inside_suggestion: ["has_suggestion", "no_suggestion"]
}
let current_state = "no_suggestion";
const set_state = (to) => {
  const available_states = state_machine[current_state]
  if (!available_states.includes(to) && current_state !== to) throw Error(`Not a valid state in ${current_state}: ${to}`);
  current_state = to;
  console.log("State is now", current_state);
}
let inside_suggestion_match = [];

let suggested_text_on_deck = [];
const [entry, suggestion, uwr_el, vcr_el, wld_el, score_el, anchor_el] = [
  document.getElementById("entry"),
  document.getElementById("suggestion"),
  document.getElementById("uwr"),
  document.getElementById("vcr"),
  document.getElementById("wld"),
  document.getElementById("score"),
  document.getElementById("anchor")
];

const word_to_token = Object.entries(token_to_word).reduce((acc, [token, word]) => {
  acc[word] = token;
  return acc;
}, {});

const get_word = (word=entry.value) => {
  let last_three_words = word.trim().split(" ");
  return slugify(last_three_words.slice(-3), "_");
};

const set_suggested_word_class = (score) => {
  suggestion.classList.remove("two_word");
  suggestion.classList.remove("three_word");
  if (score < HIGH_SCORE_THRESHOLD) return suggestion.classList.add("three_word");
  if (score < MED_SCORE_THRESHOLD) return suggestion.classList.add("two_word");
  return
}

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
  suggested_text_on_deck = [];
  suggestion.classList.remove("two_word");
  suggestion.classList.remove("three_word");
  set_state("no_suggestion")
}

const get_anchor = () => {
  const last_word = entry.value.trim().split(" ").reverse()[0];
  return slugify(last_word, "_");
}

const five_words_typed = () => {
  let last_sentence = entry.value.trim().split(".").reverse()[0];
  let last_sentence_parts = last_sentence.split(" ").filter(x => x !== "");
  return last_sentence_parts.length > 4
}

const compute_properties = (string) => {
  const words = string.toLowerCase().match(/\b(\w+)\b/g) || [];
  const uniqueWords = new Set(words);
  const uwr = uniqueWords.size / (words.length * 1.00) || 0.0;

  const vowels = string.match(/[aeiou]/gi) || [];
  const consonants = string.match(/[bcdfghjklmnpqrstvwxyz]/gi) || [];
  const vcr = vowels.length / consonants.length || 0;

  const wld = { "<=3": 0, "4": 0, "5": 0, "6": 0, ">=7": 0 };
  words.forEach(word => {
    const length = word.length;
    if (length <= 3) wld["<=3"] += 1;
    else if (length === 4) wld["4"] += 1;
    else if (length === 5) wld["5"] += 1;
    else if (length === 6) wld["6"] += 1;
    else if (length >= 7) wld[">=7"] += 1;
  });

  // Normalize counts to frequencies
  for (const key in wld) {
    wld[key] = wld[key] || 0;
  }

  uwr_el.innerText = uwr;
  vcr_el.innerText = vcr;
  wld_el.innerText = `<=3:${wld['<=3']}, 4:${wld['4']}, 5:${wld['5']}, 6:${wld['6']}, <=7:${wld['>=7']}, `;

  return { uwr, vcr, wld };
}

const calculateSimilarity = (inputProps, dictProps) => {
  const use_uwr = false;
  const use_vcr = true;
  const use_wld = true;
  let total_possible = 0
  let score = 0;
  // Compare uwr
  if (use_uwr) {
    score += Math.abs(inputProps.uwr - dictProps.uwr);
    total_possible += 1;
  }

  // Compare vcr
  if (use_vcr) {
    score += Math.abs(inputProps.vcr - dictProps.vcr);
    total_possible += 1;
  }


  // Compare wld
  if (use_wld) {
    Object.keys(inputProps.wld).forEach(key => {
      score += Math.abs((inputProps.wld[key] || 0) - (dictProps.wld[key] || 0));
      total_possible += 1;
    });
  }

  score_el.innerText = score;
  anchor_el.innerHTML = get_anchor();
  set_suggested_word_class(score);
  return score;
};

const get_suggestion = (string) => {
  const properties = compute_properties(string);
  const anchor = get_anchor();
  const anchor_as_token = word_to_token[anchor];

  const contexts = dictionary_anchors[anchor_as_token];
  if (!contexts) return [];

  let scoredEntries = contexts.reduce((acc, context) => {
    const dictProps = dictionary_properties[context];
    if (dictProps) {
      const score = calculateSimilarity(properties, dictProps);
      acc.push({ completion: dictProps.completion.split(" ").map(c => token_to_word[c]).join(" "), score });
    }
    return acc;
  }, []);

  // Sort by score, then map to completion strings
  return scoredEntries
    .sort((a, b) => a.score - b.score)
    .map(entry => entry.completion);
};

const use_suggestion = (event=undefined) => {
  const space = entry.value.split("").reverse()[0] === " " ? "" : " ";
  const suggestion = suggested_text_on_deck.shift();
  if (!suggestion) return;
  if (current_state === "inside_suggestion") {
    const toReplaceInReverse = inside_suggestion_match[0].split("").reverse().join("");
    const reversedEntry = entry.value.split("").reverse().join("");
    const newEntryReversed = reversedEntry.replace(toReplaceInReverse, suggestion.split("").reverse().join(""))
    const entryForwards = newEntryReversed.split("").reverse().join("");
    entry.value = entryForwards
  }
  else {
    entry.value = entry.value + space + suggestion + " ";
  }
  clear_suggestion();
}

entry.addEventListener("keydown", (event) => {
  if (event.key === "Tab") {
    event.preventDefault();
    use_suggestion();
  }
});

entry.addEventListener("keydown", (event) => {
  if (event.key === "Shift") {
    event.preventDefault();
    suggested_text_on_deck.push(suggested_text_on_deck.shift());
    suggestion.innerHTML = suggested_text_on_deck[0] || "...";
  }
});

suggestion.addEventListener("click", () => {
  use_suggestion();
  entry.focus();
  check_for_suggestion();
});

const cut_after_punctuation = (word_parts, delimiter) => {
  let split_up = word_parts.join(" ").split(delimiter).pop().trim();
  return split_up.split(" ").filter(word => word);
}

const find_a_suggestion = (word_parts) => {
  let suggested_words;

  // word_parts = cut_after_punctuation(word_parts, ".");
  // word_parts = cut_after_punctuation(word_parts, ",");

  suggested_words = get_suggestion(word_parts.join(" "));
  if (suggested_words.length) {
    return suggested_words
  }
  word_parts.shift();
  if (!word_parts.length) return false;
  return find_a_suggestion(word_parts)
}

const check_for_suggestion = () => {
  let word = get_word();
  if (word === "") return clear_suggestion();

  let suggested_words = find_a_suggestion(entry.value.trim().split(" ").slice(-10));

  if (!suggested_words.length) {
    set_state("no_suggestion");
    return clear_suggestion();
  }
  set_state("has_suggestion");
  suggested_text_on_deck = suggested_words;
  suggestion.innerHTML = suggested_words[0];
}

const filter_on_suggested_text_on_deck = (e) => {
  let last_word = entry.value.trim().split(" ").pop()
  if (inside_suggestion_match.length) {
    last_word = inside_suggestion_match[0] + e.key;
  }  
  if (!suggested_text_on_deck.length) return
  // Find the index of the first item that starts with the last word
  const matchIndex = suggested_text_on_deck.findIndex(item => item.startsWith(last_word));
  console.log(matchIndex, suggested_text_on_deck)

  if (matchIndex > -1) {
    // If a match is found, move the matching item to the beginning of the array
    const matchedItem = suggested_text_on_deck.splice(matchIndex, 1)[0]; // Remove the item from its current position
    suggested_text_on_deck.unshift(matchedItem); // Insert the item at the start of the array
    inside_suggestion_match = [last_word, entry.value.length];
    set_state("inside_suggestion");
  }
  else {
    inside_suggestion_match = []
    return set_state("no_suggestion");
  }
  suggestion.innerHTML = suggested_text_on_deck[0];
}

entry.addEventListener("keyup", (e) => {
  if (e.key === " ") {
    if (false && current_state === "inside_suggestion") {
      set_state("no_suggestion");
    }
  }

  if (e.key != "Shift" && e.key != "Tab") {
    if (!five_words_typed()) return clear_suggestion();
    if (current_state === "has_suggestion" || current_state === "inside_suggestion") {
      return filter_on_suggested_text_on_deck(e);
    }
    else {
      return check_for_suggestion();
    }
  }
});