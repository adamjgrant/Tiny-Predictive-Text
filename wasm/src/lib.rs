use rmp_serde::decode::from_slice;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use wasm_bindgen::prelude::*;
use serde_wasm_bindgen::to_value;

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
        Ok(tokens) => to_value(&tokens).map_err(|e| e.into()),
        Err(e) => Err(e.to_string().into()),
    }
}

#[wasm_bindgen]
pub fn get_predictive_text(input: &str) -> Result<JsValue, JsValue> {
    // Placeholder: Logic to generate predictive text based on the input string
    let predictive_texts: Vec<&str> = Vec::new(); // Example: replace with actual logic to generate texts

    // Convert the Rust Vec of strings to JsValue
    to_value(&predictive_texts).map_err(|e| e.into())
}
