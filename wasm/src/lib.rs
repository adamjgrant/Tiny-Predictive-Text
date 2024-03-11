use rmp_serde::decode::from_slice;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use wasm_bindgen::prelude::*;
use serde_wasm_bindgen::to_value;
use lazy_static::lazy_static;
use std::sync::Mutex;

// Represents the top-level structure: a map from integers to nodes
type Dictionary = HashMap<i32, Node>; // Renamed from TopLevel for clarity

#[derive(Serialize, Deserialize, Debug)]
#[serde(untagged)]
enum Node {
    Value(i32),
    Map(HashMap<i32, Node>),
    List(Vec<ListItem>),
}

#[derive(Serialize, Deserialize, Debug)]
struct ListItem {
    #[serde(rename = "0")]
    leaf: i32,
    #[serde(rename = "1")]
    items: Option<Vec<Item>>,
    #[serde(rename = "2")]
    numbers: Option<Vec<i32>>,
}

#[derive(Serialize, Deserialize, Debug)]
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
            *global_dict = Some(dictionary);
            Ok(JsValue::TRUE) // Indicate success differently if needed
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

lazy_static! {
  // Use Mutex to safely access and modify the dictionary across threads
  static ref INVERTED_TOKEN_DICT: Mutex<HashMap<String, i32>> = Mutex::new(HashMap::new());
  static ref GLOBAL_DICTIONARY: Mutex<Option<Dictionary>> = Mutex::new(None);
}

fn get_inverted_token_dict() -> HashMap<String, i32> {
  let dict_lock = INVERTED_TOKEN_DICT.lock().unwrap();
  dict_lock.clone() // Cloning here for simplicity; consider other patterns for large dictionaries
}

#[derive(Serialize, Debug)]
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

fn acronymize_context(words: Vec<&str>) -> String {
  words.iter()
      .filter_map(|word| word.chars().next())
      .collect::<String>()
      .to_lowercase()
}

// Updating the process_input function to use these helpers
fn process_input(input: &str) -> PredictiveTextContext {
  let sanitized_input = sanitize_text(input);
  let words: Vec<&str> = sanitized_input.split_whitespace().collect();

  // Ensure there's at least one word to use as anchor
  if let Some(anchor) = words.last() {
      // Sanitize and lookup the anchor token
      let anchor_token = dict.get(&sanitize_text(anchor)).cloned().unwrap_or(-1);

      // Compute first level context
      let first_level_words = words.iter().rev().skip(1).take(3).collect::<Vec<_>>();
      let first_level_context = acronymize_context(first_level_words);

      // Compute second level context
      let second_level_start = words.len().saturating_sub(7).max(0);
      let second_level_words = exclude_words(words.iter().skip(second_level_start).take(3).collect());
      let second_level_context = acronymize_context(second_level_words);

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

fn filter_dictionary_on_anchor(processed_input: &PredictiveTextContext) -> (PredictiveTextContext, Option<&Node>) {
  // Access the global dictionary. Assuming it's loaded into GLOBAL_DICTIONARY.
  let global_dict_lock = INVERTED_TOKEN_DICT.lock().unwrap();
  let global_dict = global_dict_lock.as_ref().expect("Global dictionary not loaded");

  // Attempt to retrieve the node corresponding to the anchor token from the global dictionary
  let filtered_node = global_dict.get(&processed_input.anchor_token);

  // Create a new instance of PredictiveTextContext with potential updates
  let updated_context = PredictiveTextContext {
      // Carry over all existing fields from processed_input
      anchor: processed_input.anchor.clone(),
      anchor_token: processed_input.anchor_token,
      first_level_context: processed_input.first_level_context.clone(),
      second_level_context: processed_input.second_level_context.clone(),
      // Update the prediction field or any other field as necessary
      prediction: processed_input.prediction.clone(),
  };

  // Return the updated context along with the filtered node (if found)
  (updated_context, filtered_node)
}

fn match_first_level_context(
  first_level_context: &str, 
  filtered_dict: &Node, 
  dict_token_to_string: &HashMap<i32, String>
) -> Option<&Node> {
  // Convert filtered_dict to a string-based representation if necessary
  // Assuming filtered_dict somehow allows access to the next level keys
  
  // Placeholder: Transform filtered_dict if necessary to work with strings

  // Exact match
  if let Some(node) = filtered_dict.next_level.get(first_level_context) {
      return Some(node);
  }

  // Closest match by one character difference or most characters in common
  let closest_match = filtered_dict.next_level.keys()
      .map(|key| dict_token_to_string.get(key).unwrap_or(&"".to_string()))
      .filter(|&key_str| /* your logic to determine closeness */ false)
      .next(); // Assuming this gets the closest match key as &str

  // Return the node corresponding to the closest match
  closest_match.and_then(|key| filtered_dict.next_level.get(key))
}


fn filter_on_first_level_context( processed_input: &PredictiveTextContext, anchor_filtered_dictionary: Option<&Node>,) -> (PredictiveTextContext, Option<&Node>) {
  // Access the global inverted token dictionary to convert token IDs to strings
  let dict_lock = INVERTED_TOKEN_DICT.lock().unwrap();
  let dict_token_to_string = dict_lock.clone(); // Clone for usage in this context

  // Continue with the function implementation
  if let Some(filtered_dict) = anchor_filtered_dictionary {
      let first_level_context = &processed_input.first_level_context;
      // Assuming match_first_level_context is defined and uses dict_token_to_string
      let first_level_context_filtered_node = match_first_level_context(
          first_level_context,
          filtered_dict,
          &dict_token_to_string
      );

      // Clone processed_input to create a potentially updated context
      let updated_context = PredictiveTextContext {
          anchor: processed_input.anchor.clone(),
          anchor_token: processed_input.anchor_token,
          first_level_context: processed_input.first_level_context.clone(),
          second_level_context: processed_input.second_level_context.clone(),
          prediction: processed_input.prediction.clone(), // Initially empty, updated later
      };

      // Return both the updated context and the node filtered by the first level context
      (updated_context, first_level_context_filtered_node)
  } else {
      // Return empty context if input is not sufficient or no anchor filtered dictionary is available
      (processed_input.clone(), None)
  }
}

fn filter_on_second_level_context( processed_input: &PredictiveTextContext, first_level_context_filtered_dictionary: Option<&Node>) -> (PredictiveTextContext, Option<&Node>) {
  // Assuming you have access to a conversion function or method to interpret tokens to strings if needed

  let second_level_context = &processed_input.second_level_context;

  // This variable holds the potential match for second level context within the dictionary
  let second_level_context_filtered_node: Option<&Node> = None;

  if let Some(Node::Map(flc_map)) = first_level_context_filtered_dictionary {
      // Loop through each key-value pair in the FLC filtered dictionary
      for (key, value) in flc_map {
          // Convert key (if it's a token) to string and compare or directly compare if it's already a string
          // Here, you might need a mechanism to convert or match the context as you're working with a more nuanced matching logic
          // Assuming 'match_second_level_context' is a function you'd implement
          if let Some(matching_node) = match_second_level_context(second_level_context, key, value) {
              second_level_context_filtered_node = Some(matching_node);
              break; // Exit loop early if a match is found
          }
      }
  }

  // Return both the input context and the node filtered by the second level context
  // Note: This is a basic skeleton, adjust according to your actual logic and matching criteria
  (
      processed_input.clone(), // Assuming you may update the context based on this step in your actual implementation
      second_level_context_filtered_node
  )
}

#[wasm_bindgen]
pub fn get_predictive_text(input: &str) -> Result<JsValue, JsValue> {
    // Process the input to split into sanitized anchor, first and second level contexts
    let processed_input = process_input(input);

    // At this point, you would filter the global dictionary based on the processed input
    // This might involve several steps, such as:
    // 1. Filtering on the anchor token (if your design includes this step)
    let (updated_context_after_filtering_anchor, anchor_filtered_dictionary) = filter_dictionary_on_anchor(&processed_input);

    // 2. Filtering based on the first level context
    let (updated_context_after_filtering_first_level_context, first_level_context_filtered_dictionary) = filter_on_first_level_context(updated_context_after_filtering_anchor, anchor_filtered_dictionary)

    // 3. Filtering based on the second level context
    let (updated_context_after_filtering_second_level_context, second_level_context_filtered_dictionary) = filter_on_second_level_context(updated_context_after_filtering_first_level_context, first_level_context_filtered_dictionary)

    // For demonstration, let's assume filter_on_first_level_context and filter_on_second_level_context
    // are implemented to take processed_input and return something meaningful
    // let first_level_filtered = filter_on_first_level_context(&processed_input, &GLOBAL_DICTIONARY);
    // let second_level_filtered = filter_on_second_level_context(&first_level_filtered, &GLOBAL_DICTIONARY);

    // For now, simply return the processed input as a JsValue
    to_value(&updated_context_after_filtering_second_level_context).map_err(|e| e.into())
}

