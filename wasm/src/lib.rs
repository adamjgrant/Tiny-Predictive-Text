use rmp_serde::decode::from_slice;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use wasm_bindgen::prelude::*;
use serde_wasm_bindgen::to_value;
use lazy_static::lazy_static;
use std::sync::Mutex;
use std::sync::MutexGuard;
extern crate web_sys;
use strsim::levenshtein;

#[derive(Clone, Serialize, Deserialize, Debug)]
#[serde(untagged)]
enum Node {
    Value(i32),
    Map(HashMap<i32, Node>),
    List(Vec<Vec<i32>>),  // Directly support lists of lists of integers
}

#[derive(Clone, Serialize, Deserialize, Debug)]
struct ListItem {
    #[serde(rename = "0")]
    leaf: i32,
    #[serde(rename = "1")]
    items: Option<Vec<Item>>,
    #[serde(rename = "2")]
    numbers: Option<Vec<i32>>,
}

#[derive(Clone, Serialize, Deserialize, Debug)]
struct Item {
    #[serde(rename = "0")]
    leaf: i32,
    #[serde(rename = "2")]
    array: Vec<i32>,
}

#[wasm_bindgen]
pub fn load_dictionary(data: &[u8]) -> Result<JsValue, JsValue> {
    let dictionary_result: Result<Dictionary, _> = from_slice(data);
    match dictionary_result {
        Ok(dictionary) => {
            let mut global_dict = GLOBAL_DICTIONARY.lock().unwrap();
            *global_dict = Some(dictionary.clone()); // Store a copy in the global variable if needed

            // Serialize and return the loaded dictionary
            to_value(&dictionary).map_err(|e| e.into())
        },
        Err(e) => Err(e.to_string().into()),
    }
}

#[wasm_bindgen]
pub fn load_tokens(data: &[u8]) -> Result<JsValue, JsValue> {
    let tokens_result: Result<HashMap<i32, String>, _> = from_slice(data);
    match tokens_result {
        Ok(tokens) => {
            // Invert the dictionary: Map from String -> i32
            let inverted_dict: HashMap<String, i32> = tokens.into_iter().map(|(key, val)| (val, key)).collect();

            // Store the inverted dictionary for later use
            let mut global_dict = INVERTED_TOKEN_DICT.lock().unwrap(); // Lock the mutex around the global dictionary
            *global_dict = inverted_dict; // Replace the contents with the new inverted dictionary

            // Returning the inverted dictionary for demonstration; adjust as needed
            to_value(&*global_dict).map_err(|e| e.into())
        },
        Err(e) => Err(e.to_string().into()),
    }
}

type Dictionary = HashMap<i32, Node>;

lazy_static! {
    static ref INVERTED_TOKEN_DICT: Mutex<HashMap<String, i32>> = Mutex::new(HashMap::new());
    static ref GLOBAL_DICTIONARY: Mutex<Option<Dictionary>> = Mutex::new(None);
}

#[derive(Clone, Serialize, Deserialize, Debug)]
struct PredictiveTextContext {
    anchor: String,
    anchor_token: i32,
    first_level_context: String,
    second_level_context: String,
    prediction: String,
}

// Placeholder function to sanitize text (removing punctuation, making lowercase)
fn sanitize_text(text: &str) -> String {
  text.chars()
      .filter(|c| c.is_alphanumeric() || c.is_whitespace())
      .collect::<String>()
      .to_lowercase()
}

fn exclude_words<'a>(words: Vec<&'a str>) -> Vec<&'a str> {
  let exclusions = vec![
      "and", "or", "but", "if", "of", "at", "by", "for", "with", "to", "in", "on",
      "am", "is", "are", "was", "were", "be", "been", "being",
      "have", "has", "had", "having",
      "the", "a", "an",
  ];
  words.into_iter()
      .filter(|word| !exclusions.contains(word))
      .collect()
}

fn acronymize_context(words: &[&str]) -> String {
  words.iter()
      .filter_map(|word| word.chars().next())
      .collect::<String>()
      .to_lowercase()
}

// Updating the process_input function to use these helpers
fn process_input(input: &str) -> PredictiveTextContext {
  web_sys::console::log_1(&input.into());
  let sanitized_input = sanitize_text(input);
  let words: Vec<&str> = sanitized_input.split_whitespace().collect();

  // This pattern is correct for accessing the inverted dictionary.
  let inverted_dict_lock = INVERTED_TOKEN_DICT.lock().unwrap();
  let inverted_dict = &*inverted_dict_lock;

  let anchor_token = words.last()
    .and_then(|anchor| inverted_dict.get(&sanitize_text(anchor)))
    .cloned()
    .unwrap_or(-1); // This gets the ID associated with the anchor

  // Ensure there's at least one word to use as anchor
  if let Some(anchor) = words.last() {
      // Compute first level context
      let first_level_words = words.iter().rev().skip(1).take(3).map(|&word| word).collect::<Vec<&str>>();
      let first_level_context = acronymize_context(&first_level_words); // Ensure acronymize_context accepts a slice

      // Compute second level context
      let second_level_start = words.len().saturating_sub(7).max(0);
      let second_level_words = exclude_words(words.iter().skip(second_level_start).take(3).map(|&word| word).collect::<Vec<&str>>());
      let second_level_context = acronymize_context(&second_level_words); // Ensure acronymize_context accepts a slice

      PredictiveTextContext {
          anchor: anchor.to_string(),
          anchor_token,
          first_level_context,
          second_level_context,
          prediction: String::new(), // Empty initially, to be filled later
      }
  } else {
      // Return empty context if input is not sufficient
      PredictiveTextContext {
          anchor: String::new(),
          anchor_token: -1,
          first_level_context: String::new(),
          second_level_context: String::new(),
          prediction: String::new(),
      }
  }
}

fn filter_dictionary_on_anchor(processed_input: &PredictiveTextContext) -> (PredictiveTextContext, Option<Node>) {
  // Directly access the global dictionary here, assuming it's properly loaded and of the correct type.
  let global_dict = GLOBAL_DICTIONARY.lock().unwrap();
  
  // Assuming your global dictionary maps i32 to Node.
  let filtered_data = global_dict.as_ref()
      .and_then(|dict| dict.get(&processed_input.anchor_token))
      .cloned(); // Clone the Node if found.

  let updated_context = processed_input.clone();

  (updated_context, filtered_data)
}

fn match_first_level_context(
  first_level_context: &str,
  filtered_dict: &Node,
  dict_token_to_string: &HashMap<String, i32>,
) -> Option<Node> {
    if let Node::Map(sub_map) = filtered_dict {
        let mut closest_match: Option<(&Node, usize)> = None;

        for (&key, value) in sub_map {
            if let Some(key_str) = dict_token_to_string.iter().find_map(|(s, &k)| if k == key { Some(s) } else { None }) {
                let distance = levenshtein(first_level_context, key_str);

                match closest_match {
                    None => closest_match = Some((value, distance)),
                    Some((_, prev_distance)) if distance < prev_distance => closest_match = Some((value, distance)),
                    _ => (),
                }
            }
        }

        closest_match.map(|(node, _)| node.clone())
    } else {
        None
    }
}

fn filter_on_first_level_context(
  processed_input: &PredictiveTextContext,
  anchor_filtered_dictionary: &Node,
) -> (PredictiveTextContext, Option<Node>) {
  // Access the global inverted token dictionary to convert token IDs to strings
  let dict_lock = INVERTED_TOKEN_DICT.lock().unwrap();

  if let Node::Map(_sub_map) = anchor_filtered_dictionary {
      let first_level_context = &processed_input.first_level_context;
      
      let first_level_context_filtered_node = match_first_level_context(
          first_level_context,
          anchor_filtered_dictionary,
          &dict_lock // Pass reference directly without cloning
      );
      web_sys::console::log_1(&to_value(&first_level_context_filtered_node).unwrap_or_else(|_| JsValue::UNDEFINED));

      let updated_context = processed_input.clone(); // Clone processed_input to create a potentially updated context
      (updated_context, first_level_context_filtered_node) // Return both the updated context and the node
  } else {
      // Return empty context if no anchor filtered dictionary is available
      (processed_input.clone(), None)
  }
}

fn match_second_level_context(
  _second_level_context: &str, 
  _key: &i32, 
  _value: &Node,
  _dict_token_to_string: &HashMap<String, i32>, // Assuming you need this based on the pattern
) -> Option<Node> {
  // Placeholder logic: Implement the actual matching logic here
  // For demonstration, let's just return None
  None
}

fn filter_on_second_level_context(
  processed_input: &PredictiveTextContext, 
  first_level_context_filtered_dictionary: &Node
) -> (PredictiveTextContext, Option<Node>) {
  let second_level_context = &processed_input.second_level_context;

  // Initialize as None, will be updated if a matching node is found
  let mut second_level_context_filtered_node = None;

  if let Node::Map(flc_map) = first_level_context_filtered_dictionary {
      let dict_lock = INVERTED_TOKEN_DICT.lock().unwrap();

      for (&key, value) in flc_map {
          if let Some(matching_node) = match_second_level_context(second_level_context, &key, value, &dict_lock) {
              second_level_context_filtered_node = Some(matching_node.clone());
              break; // Exit loop early if a match is found
          }
      }
  }

  let updated_context = processed_input.clone();
  (updated_context, second_level_context_filtered_node)
}

#[wasm_bindgen]
pub fn get_predictive_text(input: &str) -> Result<JsValue, JsValue> {
    // web_sys::console::log_1(&input.into());

    // Process the input to split into sanitized anchor, first and second level contexts
    let processed_input = process_input(input);

    // At this point, you would filter the global dictionary based on the processed input
    // This might involve several steps, such as:
    // 1. Filtering on the anchor token (if your design includes this step)
    let (updated_context_after_filtering_anchor, anchor_filtered_dictionary) = filter_dictionary_on_anchor(&processed_input);

    // 2. Filtering based on the first level context
    let (updated_context_after_filtering_first_level_context, first_level_context_filtered_dictionary) = filter_on_first_level_context(&updated_context_after_filtering_anchor, anchor_filtered_dictionary.as_ref().unwrap());

    // let debug_info_1 = (updated_context_after_filtering_anchor, anchor_filtered_dictionary);
    // return serde_wasm_bindgen::to_value(&debug_info_1).map_err(|e| e.into());

    // 3. Filtering based on the second level context
    let (updated_context_after_filtering_second_level_context, second_level_context_filtered_dictionary) = filter_on_second_level_context(&updated_context_after_filtering_first_level_context, &first_level_context_filtered_dictionary.as_ref().unwrap());
    // Debugging: Return early after filtering based on the first level context
    // let debug_info_2 = (updated_context_after_filtering_first_level_context, first_level_context_filtered_dictionary);
    // return serde_wasm_bindgen::to_value(&debug_info_2).map_err(|e| e.into());

    // For demonstration, let's assume filter_on_first_level_context and filter_on_second_level_context
    // are implemented to take processed_input and return something meaningful
    // let first_level_filtered = filter_on_first_level_context(&processed_input, &GLOBAL_DICTIONARY);
    // let second_level_filtered = filter_on_second_level_context(&first_level_filtered, &GLOBAL_DICTIONARY);

    // For now, simply return the processed input as a JsValue
    to_value(&updated_context_after_filtering_second_level_context).map_err(|e| e.into())
}

// Where I left off:
// I think filtering on the first level context works okay. I'm now wondering whether or not its giving
// me back just the one best match at that key-level, because I'd want the second level filtering to just
// jump down a key-level and do the same with the second level context and I'm not sure that's what it's doing.
// 
// (Below is done)
// Maybe what would be useful is to get the msgpack to look right, without the score values and things we don't 
// need in the final printing. Better yet, if we can make a miniature version of it, and the token dict that we
// just use for testing. That way we can actually see where we are in the dict structure—which is super not clear
// from debugging right now.