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
}

lazy_static! {
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

fn sanitize_anchor(anchor: &str) -> String {
  anchor.chars()
        .filter(|c| c.is_alphanumeric() || c.is_whitespace()) // Keep alphanumeric and whitespace
        .collect::<String>()
        .to_lowercase()
}

fn process_input(input: &str) -> PredictiveTextContext {
  // Placeholder for the actual processing logic
  // This will involve sanitizing the input and splitting into anchor, first and second level contexts
  let global_dict_lock = GLOBAL_DICTIONARY.lock().unwrap(); // Access the global tokenized dictionary
  let global_dict = global_dict_lock.as_ref().expect("Dictionary not loaded");

  // Define the words to exclude from second level context acronym
  // ⚠️ Make sure this matches the parallel implementation in process_context_words.py
  let exclusions = ["and", "or", "but", "if", "of", "at", "by", "for", "with", "to", "in", "on", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "the", "a", "an"];

  let words: Vec<&str> = input.split_whitespace().collect();
  let anchor = words.last().unwrap().to_string();
  let anchor_token = dict.get(&*anchor).cloned().unwrap_or(-1); // Use -1 as a placeholder if not found

  PredictiveTextContext {
      anchor: anchor,
      anchor_token: anchor_token,
      first_level_context: String::new(),
      second_level_context: String::new(),
      prediction: String::new(), // Empty initially
  }
}

fn filter_dictionary_on_anchor(processed_input: &PredictiveTextContext, global_dict: &Dictionary) -> Option<&Node> {
  // Convert the anchor to a token using your inverted token dictionary
  // Lookup this token in the global dictionary and return the filtered part

  // Use anchor_token to filter the dictionary
  // TODO this should get the anchor token from the key on processed_input
  let anchor_token = processed_input.get(&anchor_token);
  
  // TODO use the variable anchor_token above to get a value from the global_dict and set equal to filtered_dict.
  let filtered_dict = global_dict.get(&anchor_token);
  None // Placeholder
}

fn filter_on_first_level_context(processed_input: &PredictiveTextContext, filtered_dict: &Node) -> Option<&Node> {
  let dict = get_inverted_token_dict(); // Token -> String dictionary

  // First level context as an acronym
  let first_level_start = words.len().saturating_sub(4).max(0);
  let first_level_context: String = words[first_level_start..words.len() - 1]
      .iter()
      .filter_map(|word| word.chars().next()) // Get the first char of each word
      .map(|c| c.to_lowercase().to_string()) // Convert to lowercase string
      .collect(); // Collect into a String, which concatenates them
  // Perform matching logic on the first level context against the filtered dictionary
  None // Placeholder
}

fn filter_on_second_level_context(processed_input: &PredictiveTextContext, further_filtered_dict: &Node) -> Option<&Node> {
  // Perform matching logic on the second level context

  // Second level context without specified words, then as an acronym
  let second_level_start = first_level_start.saturating_sub(3).max(0);
  let second_level_context: String = words[second_level_start..first_level_start]
      .iter()
      .filter(|&&word| !exclusions.contains(&word)) // Exclude specified words
      .filter_map(|word| word.chars().next()) // Get the first char of each remaining word
      .map(|c| c.to_lowercase().to_string()) // Convert to lowercase string
      .collect(); // Collect into a String, which concatenates them
  None // Placeholder
}

#[wasm_bindgen]
pub fn get_predictive_text(input: &str) -> Result<JsValue, JsValue> {
    let context = PredictiveTextContext {
        anchor,
        anchor_token,
        first_level_context,
        second_level_context,
        prediction: prediction.to_string(), // Include the prediction
    };

    // Convert the struct into JsValue
    to_value(&context).map_err(|e| e.into())
}

