// import { Tree } from './permute.js';

// Permute.js
class Tree{constructor(t){this.object=t}get one(){return this.translated_branch.one()}get permutations(){return this.translated_branch.terminal_leaves()}get translated_branch(){return new Branch(this,this.translate_main)}get translate_main(){return new Branch(this,this.object.main).translate_object}branch(t){return this.object[t]||[]}get unique_branch_name(){const t=Object.keys(this.object).reduce((t,e)=>{return e.length>t?e:t},""),e=`${t}-${Date.now()}`;return this.object[e]=[],e}}class Branch{constructor(t,e,n){this.tree=t,this.object=e,this.then_branches=n}terminal_leaves(t=""){return this.branches().length?this.leaves().reduce((e,n)=>{return e.concat(this.branches().reduce((e,r)=>{return e.concat(new Branch(this.tree,r).terminal_leaves(`${t}${n}`))},[]))},[]):this.leaves().map(e=>`${t}${e}`)}one(t=""){const e=`${t}${this.leaves(!0)}`;return this.branches().length?new Branch(this.tree,this.branches(!0)).one(e):e}leaves(t=!1){let e=this.object.filter(t=>new Leaf(t).is_string)||[];const n=e.length?e:[""];return t?n[~~(n.length*Math.random())]:n}branches(t=!1){const e=new Leaf(this.object);e.is_directive&&(this.object=[this.translate_directive(e)]),e.is_string&&(this.object=[this.object]);const n=this.object.filter(t=>new Leaf(t).is_branch);return t?n[~~(n.length*Math.random())]:n}translate_directive(t){return t.has_directive("branch")?this.translate_branch_reference(t):t.has_directive("ps")?this.translate_ps_reference(t):void 0}get translate_object(){const t=new Leaf(this.object);return t.is_directive?this.translate_directive(t):(this.is_terminal_branch&&void 0!==this.then_branches&&this.object.push(this.then_branches),this.object.map(t=>{const e=new Leaf(t);if(e.has_directive("branch"))return this.translate_branch_reference(e);if(e.has_directive("ps"))return this.translate_ps_reference(e);if(e.is_branch){const t=new Branch(this.tree,e.node);return t.is_terminal_branch||(t.then_branches=this.then_branches),t.translate_object}return e.node}))}get is_terminal_branch(){return!(this.branches().length&&void 0!==this.then_branches)&&this.object.every(t=>new Leaf(t).is_string)}translate_branch_reference(t){const e=this.duplicate_branch(this.tree.branch(t.node.branch)),n=new Branch(this.tree,e,this.then_branches);if(t.has_directive("then")){const e=this.translate_then_reference(t);n.prepend_then_branch(e)}return n.translate_object}translate_then_reference(t){let e=t.node.then;return"String"===e.constructor.name&&(e=[e]),new Branch(this.tree,e).translate_object}translate_ps_reference(t){return new PermyScript(t.node.ps).compile}duplicate_branch(t){return JSON.parse(JSON.stringify(t))}prepend_then_branch(t){if(void 0!==t){const e=new Branch(this.tree,t,this.then_branches).translate_object;return this.is_terminal_branch?this.object=this.deep_end(t):this.prepend_to_non_terminal_branch(e)}}prepend_to_non_terminal_branch(t){const e=this.object.filter(t=>{return!new Leaf(t).is_string}).map(e=>{const n=new Branch(this.tree,e,this.then_branches).translate_object,r=this.duplicate_branch(this.tree.object),i=this.tree.unique_branch_name;return r.main={branch:i,then:t},r[i]=n,new Tree(r).translate_main});return this.object=[...this.leaves(),...e]}deep_end(t){if(!this.branches().length)return this.object.push(t),this.object;const e=this.branches().map(e=>{const n=new Branch(this.tree,e);return n.deep_end(t),n.object});return this.object=[...this.leaves(),...e]}}class Leaf{constructor(t){this.node=t}get is_branch(){return Array.isArray(this.node)}get is_string(){return"String"===this.node.constructor.name}get is_directive(){return this.has_directive("branch")||this.has_directive("ps")}has_directive(t="branch"){return"object"==typeof this.node&&void 0!==this.node[t]}}class PermyScript{constructor(t){this.string=t,this.tree_object={main:[]},this.last_unique_branch_name="0"}get unique_branch_name(){return this.last_unique_branch_name=String(parseInt(this.last_unique_branch_name)+1),this.last_unique_branch_name}get break_into_parts(){const t=[],e=this.string.split("");return e.reduce((n,r,i)=>{return r.match(/\(/)?(t.push(n),r):r.match(/\)/)?(t.push(n+r),""):i!==e.length-1?n+r:void t.push(n+r)},""),this.tree_object.main=t,this}get convert_parens(){return this.tree_object.main=this.tree_object.main.map(t=>{return new Part(t)}),this}get delegate_to_branches(){let t=new Tree({main:[]});return this.tree_object.main.forEach(e=>{if(e.is_directive){const n=this.unique_branch_name;t.object[n]=e.branch,t=new Tree(t.object);const r=t.translated_branch,i={branch:n};r.deep_end(i),t.object.main=r.object,t=new Tree(t.object)}else{let n=t.translated_branch;"[]"===JSON.stringify(n.object)?n=new Branch(t,e.branch):n.deep_end(e.branch),t.object.main=n.object,t=new Tree(t.object)}}),this.tree_object=t.object,this}get compile(){return new Tree(this.break_into_parts.convert_parens.delegate_to_branches.tree_object).translate_main}}class Part{constructor(t){this.string=t}get is_directive(){return"("===this.string.substr(0,1)&&")"===this.string.substring(this.string.length,this.string.length-1)}get branch(){return this.string.replace(/[()]/g,"").split("|")}}
// import { dictionary } from './dictionary-8.5MB.js';
// import { dictionary } from './dictionary-3.6MB.js';
import { dictionary } from './dictionary.js';

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
