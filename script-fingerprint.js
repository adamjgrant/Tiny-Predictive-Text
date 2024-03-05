import { dictionary_fingerprint as dictionary } from './dictionary-fingerprint.js';

let suggested_text_on_deck = "";
const [entry, suggestion, uwr_el, vcr_el, wld_el] = [
  document.getElementById("entry"),
  document.getElementById("suggestion"),
  document.getElementById("uwr"),
  document.getElementById("vcr"),
  document.getElementById("wld"),
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
}

const compute_properties = (string) => {
  const words = string.toLowerCase().match(/\b(\w+)\b/g) || [];
  const uniqueWords = new Set(words);
  const uwr = uniqueWords.size / (words.length + 1.00) || 0.0;

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
    wld[key] = wld[key] / words.length || 0;
  }

  uwr_el.innerText = uwr;
  vcr_el.innerText = vcr;
  wld_el.innerText = `<=3:${wld['<=3']}, 4:${wld['4']}, 5:${wld['5']}, 6:${wld['6']}, <=7:${wld['>=7']}, `;

  return { uwr, vcr, wld };
}

const calculateSimilarity = (inputProps, dictProps) => {
  let score = 0;
  // Compare uwr
  score += Math.abs(inputProps.uwr - dictProps.uwr);
  // Compare vcr
  score += Math.abs(inputProps.vcr - dictProps.vcr);
  // Compare wld
  Object.keys(inputProps.wld).forEach(key => {
    score += Math.abs((inputProps.wld[key] || 0) - (dictProps.wld[key] || 0));
  });
  return score;
};

const get_suggestion = (string) => {
  const properties = compute_properties(string);
  let closestMatch = null;
  let lowestScore = Infinity;

  // Assuming dictionary is accessible and loaded
  Object.entries(dictionary).forEach(([key, dictProps]) => {
    const score = calculateSimilarity(properties, dictProps);
    if (score < lowestScore) {
      lowestScore = score;
      closestMatch = key;
    }
  });

  // Optionally, you can return the completion of the closest match
  return closestMatch ? dictionary[closestMatch].completion : null;
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
  return // TODO Needed?
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

  let suggested_word = find_a_suggestion(entry.value.trim().split(" ").slice(-10));

  if (!suggested_word) {
    return clear_suggestion();
  }
  suggested_text_on_deck = suggested_word;
  suggestion.innerHTML = suggested_word;
}

entry.addEventListener("keyup", check_for_suggestion);
