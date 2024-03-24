use rmp_serde::decode::from_slice;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use wasm_bindgen::prelude::*;
use serde_wasm_bindgen::to_value;
use lazy_static::lazy_static;
use std::sync::Mutex;
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
            // The original tokens HashMap is the non-inverted dictionary
            let non_inverted_dict = tokens.clone(); // Clone it to keep ownership for further use

            // Invert the dictionary: Map from String -> i32
            let inverted_dict: HashMap<String, i32> = tokens.into_iter().map(|(key, val)| (val, key)).collect();

            // Store the non-inverted dictionary for later use
            let mut token_dict_lock = TOKEN_DICT.lock().unwrap(); // Lock the mutex around the global token dictionary
            *token_dict_lock = non_inverted_dict.clone(); // Replace the contents with the new non-inverted dictionary

            // Store the inverted dictionary for later use
            let mut global_inverted_dict = INVERTED_TOKEN_DICT.lock().unwrap(); // Lock the mutex around the global inverted dictionary
            *global_inverted_dict = inverted_dict; // Replace the contents with the new inverted dictionary

            // Serialize and return the non-inverted dictionary to JavaScript
            to_value(&non_inverted_dict).map_err(|e| e.into())
        },
        Err(e) => Err(e.to_string().into()),
    }
}


type Dictionary = HashMap<i32, Node>;

lazy_static! {
    static ref TOKEN_DICT: Mutex<HashMap<i32, String>> = Mutex::new(HashMap::new());
    static ref INVERTED_TOKEN_DICT: Mutex<HashMap<String, i32>> = Mutex::new(HashMap::new());
    static ref GLOBAL_DICTIONARY: Mutex<Option<Dictionary>> = Mutex::new(None);
}

#[derive(Clone, Serialize, Deserialize, Debug)]
struct PredictiveTextContext {
    anchor: String,
    anchor_token: i32,
    first_level_context: String,
    second_level_context: String,
    prediction: Vec<String>,
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

fn process_input(input: &str) -> PredictiveTextContext {
  let sanitized_input = sanitize_text(input);
  let words: Vec<&str> = sanitized_input.split_whitespace().collect();

  let anchor_token = words.last()
      .map(|&anchor| INVERTED_TOKEN_DICT.lock().unwrap().get(&sanitize_text(anchor)).cloned().unwrap_or(-1))
      .unwrap_or(-1); // This gets the ID associated with the anchor if present

  if let Some(anchor) = words.last() {
      // Compute first level context if there are 2 or more words (1 or more + anchor)
      let first_level_context = if words.len() >= 2 {
          let first_level_words = words.iter()
              .take(words.len() - 1) // Exclude the anchor from the context
              .cloned() // Correctly clone each &str reference
              .collect::<Vec<&str>>(); // Collect the words directly
          acronymize_context(&first_level_words)
      } else {
          String::new()
      };
    

      // Compute second level context
      let second_level_context = if words.len() > 3 { // Ensure there are words apart from the first level context
          let max_lookback = words.len().saturating_sub(4).saturating_sub(20).max(0);
          let potential_second_level_words = words.iter()
              .skip(max_lookback)
              .take(words.len() - 4) // Take all words up to the start of the first level context
              .cloned()
              .collect::<Vec<&str>>();

          let filtered_second_level_words = exclude_words(potential_second_level_words)
              .into_iter()
              .rev() // Reverse to get the words closest to the first level context
              .take(3) // Take the first three words after filtering and reversing
              .collect::<Vec<&str>>();

          acronymize_context(&filtered_second_level_words.iter().rev().cloned().collect::<Vec<&str>>())
      } else {
          String::new()
      };

      PredictiveTextContext {
          anchor: anchor.to_string(),
          anchor_token,
          first_level_context,
          second_level_context,
          prediction: Vec::<String>::new(), // Empty initially, to be filled later
      }
  } else {
      // Return empty context if input is not sufficient
      PredictiveTextContext {
          anchor: String::new(),
          anchor_token: -1,
          first_level_context: String::new(),
          second_level_context: String::new(),
          prediction: Vec::<String>::new(),
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

fn match_x_level_context(
  x_level_context: &str,
  filtered_dict: &Node,
  dict_token_to_string: &HashMap<String, i32>,
) -> Option<Node> {
    if let Node::Map(sub_map) = filtered_dict {
        let mut closest_match: Option<(&Node, usize)> = None;

        for (&key, value) in sub_map {
            if let Some(key_str) = dict_token_to_string.iter().find_map(|(s, &k)| if k == key { Some(s) } else { None }) {
                let distance = levenshtein(x_level_context, key_str);

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

fn filter_on_x_level_context(
  processed_input: &PredictiveTextContext,
  filtered_dictionary: &Node,
) -> (PredictiveTextContext, Option<Node>) {
  // Access the global inverted token dictionary to convert token IDs to strings
  let dict_lock = INVERTED_TOKEN_DICT.lock().unwrap();

  if let Node::Map(_sub_map) = filtered_dictionary {
      let first_level_context = &processed_input.first_level_context;

      let context_filtered_node = match_x_level_context(
          first_level_context,
          filtered_dictionary,
          &dict_lock // Pass reference directly without cloning
      );
      // web_sys::console::log_1(&to_value(&context_filtered_node).unwrap_or_else(|_| JsValue::UNDEFINED));

      let updated_context = processed_input.clone(); // Clone processed_input to create a potentially updated context
      (updated_context, context_filtered_node) // Return both the updated context and the node
  } else {
      // Return empty context if no anchor filtered dictionary is available
      (processed_input.clone(), None)
  }
}

fn extract_predictions(filtered_node: Option<Node>) -> Vec<String> {
  let dict_lock = TOKEN_DICT.lock().unwrap(); // Access the token dictionary

  match filtered_node {
      Some(Node::List(list_of_lists)) => {
          // web_sys::console::log_1(&"Direct List of lists:".into());
          list_of_lists.iter().map(|list| {
              list.iter().map(|&id| {
                  let result = dict_lock.get(&id).cloned().unwrap_or_default();
                  // Optionally log each ID and its corresponding string
                  // web_sys::console::log_1(&format!("ID: {}, String: {}", id, result).into());
                  result
              }).collect::<Vec<String>>().join(" ")
          }).collect::<Vec<String>>()
      },
      Some(Node::Map(sub_map)) => sub_map.iter().flat_map(|(_key, node)| {
          match node {
              Node::List(list_of_lists) => {
                  // web_sys::console::log_1(&"Nested List of lists in Map:".into());
                  list_of_lists.iter().map(|list| {
                      list.iter().map(|&id| {
                          let result = dict_lock.get(&id).cloned().unwrap_or_default();
                          result
                      }).collect::<Vec<String>>().join(" ")
                  }).collect::<Vec<String>>()
              },
              _ => vec![],
          }
      }).collect(),
      _ => vec![],
  }
}


#[wasm_bindgen]
pub fn get_predictive_text(input: &str) -> Result<JsValue, JsValue> {
  let processed_input = process_input(input);

  // Filter on the anchor token
  let (updated_context_after_filtering_anchor, anchor_filtered_dictionary) = filter_dictionary_on_anchor(&processed_input);

  //web_sys::console::log_1(&"Anchor filtered dictionary:".into());
  //web_sys::console::log_1(&to_value(&anchor_filtered_dictionary).unwrap_or(JsValue::UNDEFINED));

  // Check if a Node was returned; if not, return the processed_input as is
  if let Some(anchor_dict) = anchor_filtered_dictionary {
      // If we do have an anchor dictionary, proceed with further filtering

      // Filtering based on the first level context
      let (updated_context_after_filtering_first_level_context, first_level_context_filtered_dictionary) = filter_on_x_level_context(&updated_context_after_filtering_anchor, &anchor_dict);

      // Filtering based on the second level context, if there was a dictionary from the first level filtering
      if let Some(first_level_dict) = first_level_context_filtered_dictionary {
          let (mut final_context, second_level_context_filtered_dictionary) = filter_on_x_level_context(&updated_context_after_filtering_first_level_context, &first_level_dict);

          // Log the second level context filtered dictionary
          // web_sys::console::log_1(&"Second level context filtered dictionary:".into());
          // web_sys::console::log_1(&to_value(&second_level_context_filtered_dictionary).unwrap_or_else(|_| JsValue::UNDEFINED));

          // Extract predictions
          let predictions = extract_predictions(second_level_context_filtered_dictionary);

          // web_sys::console::log_1(&"Predictions:".into());
          // web_sys::console::log_1(&to_value(&predictions).unwrap_or_else(|_| JsValue::UNDEFINED));
          
          // Set the predictions key on final_context to `predictions`
          final_context.prediction = predictions; // Assigning the predictions directly to the `prediction` field

          // Serialize and return the final context after all filtering
          return to_value(&final_context).map_err(|e| e.into());
      }
  }

  // Fallback: Serialize and return the initial or latest context available
  to_value(&updated_context_after_filtering_anchor).map_err(|e| e.into())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_first_level_context() {
        let input = "Apple banana carrot orange";
        let context = process_input(input);

        // Assuming the desired first level context is computed from the last three words,
        // and it should be "bco" based on the acronym function you have.
        // This assertion checks if the first level context is as expected.
        assert_eq!(context.first_level_context, "abc", "The first level context did not match the expected value.");
    }

    #[test]
    fn test_first_level_short_context() {
        let input = "carrot orange";
        let context = process_input(input);

        // Assuming the desired first level context is computed from the last three words,
        // and it should be "bco" based on the acronym function you have.
        // This assertion checks if the first level context is as expected.
        assert_eq!(context.first_level_context, "c", "The first level context did not match the expected value.");
    }

    #[test]
    fn test_second_level_context() {
        let input = "Xylophone Yacht is Zebra Apple banana carrot orange";
        let context = process_input(input);

        // Assuming the desired first level context is computed from the last three words,
        // and it should be "bco" based on the acronym function you have.
        // This assertion checks if the first level context is as expected.
        assert_eq!(context.second_level_context, "xyz", "The second level context did not match the expected value.");
    }

    #[test]
    fn test_anchor_only() {
        let input = "orange";
        let context = process_input(input);

        // Assuming the desired first level context is computed from the last three words,
        // and it should be "bco" based on the acronym function you have.
        // This assertion checks if the first level context is as expected.
        assert_eq!(context.first_level_context, "", "The first level context did not match the expected value.");
        assert_eq!(context.second_level_context, "", "The second level context did not match the expected value.");
    }

    #[test]
    fn test_close_match_x_level_context() {
        // Setup a simple Node::Map with a few keys
        let mut filtered_dict = HashMap::new();
        filtered_dict.insert(1, Node::Value(10));
        filtered_dict.insert(2, Node::Value(20));
        let node = Node::Map(filtered_dict);

        // Setup a dict_token_to_string mapping IDs to words
        // Assume "apple" is ID 1 and "banana" is ID 2
        let mut dict_token_to_string = HashMap::new();
        dict_token_to_string.insert("apple".to_string(), 1);
        dict_token_to_string.insert("banana".to_string(), 2);

        // A string that's a close match to "apple" but not an exact match
        let x_level_context = "pplea";

        // Call match_x_level_context
        let result = match_x_level_context(&x_level_context, &node, &dict_token_to_string);

        // Assert the expected Node is returned, indicating a match with "apple"
        match result {
            Some(Node::Value(val)) => assert_eq!(val, 10, "The function did not match the closest key correctly."),
            _ => panic!("The function did not return the expected Node type."),
        }
    }
}