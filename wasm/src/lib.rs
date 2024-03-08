use wasm_bindgen::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use rmp_serde::decode::from_read_ref;
use serde_wasm_bindgen::to_value;
// Optional: Use web_sys for logging if needed.

#[derive(Serialize, Deserialize, Debug)]
#[serde(untagged)]
enum Node {
    Leaf(i32),
    Node(HashMap<i32, Node>),
    NodeList(Vec<Item>),
}

#[derive(Serialize, Deserialize, Debug)]
struct Item {
    #[serde(rename = "0")]
    leaf: i32,
    #[serde(rename = "2")]
    list: Vec<i32>,
}

#[derive(Serialize, Deserialize, Debug)]
struct Dictionary {
    #[serde(flatten)]
    inner: HashMap<i32, Node>,
}

#[wasm_bindgen]
pub fn load_dictionary(data: &[u8]) -> Result<JsValue, JsValue> {
    // Directly infer the type based on the context without specifying it in angle brackets.
    let dictionary_result: Result<Dictionary, _> = from_read_ref(data);
    match dictionary_result {
        Ok(dictionary) => to_value(&dictionary).map_err(JsValue::from),
        Err(e) => Err(JsValue::from_str(&e.to_string())),
    }
}

#[wasm_bindgen]
pub fn load_tokens(data: &[u8]) -> Result<JsValue, JsValue> {
    // Similarly, let Rust infer the type for tokens.
    let tokens_result: Result<HashMap<i32, String>, _> = from_read_ref(data);
    match tokens_result {
        Ok(tokens) => to_value(&tokens).map_err(JsValue::from),
        Err(e) => Err(JsValue::from_str(&e.to_string())),
    }
}

