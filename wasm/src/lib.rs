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
        Ok(dictionary) => to_value(&dictionary).map_err(|e| e.into()),
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

fn get_inverted_token_dict() -> HashMap<String, i32> {
  let dict_lock = INVERTED_TOKEN_DICT.lock().unwrap();
  dict_lock.clone() // Cloning here for simplicity; consider other patterns for large dictionaries
}

#[derive(Serialize, Debug)]
struct PredictiveTextContext {
    anchor: String,
    first_level_context: Vec<String>,
    second_level_context: Vec<String>,
}

#[wasm_bindgen]
pub fn get_predictive_text(input: &str) -> Result<JsValue, JsValue> {
    let dict = get_inverted_token_dict();
    let words: Vec<&str> = input.split_whitespace().collect();
    let tokens: Vec<i32> = words.iter().filter_map(|&word| dict.get(word).cloned()).collect();

    let (anchor, first_level_context, second_level_context) = if words.len() > 3 {
        // Anchor
        let anchor = words.last().unwrap().to_string();
        
        // First level context
        let first_level_start = words.len().saturating_sub(4).max(0);
        let first_level_context: Vec<String> = words[first_level_start..words.len() - 1]
                                                .iter().map(|&word| word.to_string()).collect();
        
        // Second level context
        let second_level_start = first_level_start.saturating_sub(3).max(0);
        let second_level_context: Vec<String> = words[second_level_start..first_level_start]
                                                 .iter().map(|&word| word.to_string()).collect();
        
        (anchor, first_level_context, second_level_context)
    } else {
        ("".to_string(), vec![], vec![]) // Default values if not enough words
    };

    let context = PredictiveTextContext {
        anchor,
        first_level_context,
        second_level_context,
    };

    // Convert the struct into JsValue
    to_value(&context).map_err(|e| e.into())
}
