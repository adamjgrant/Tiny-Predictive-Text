// Updated import to reflect change from `from_read_ref` to `from_slice`.
use rmp_serde::decode::from_slice;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use wasm_bindgen::prelude::*;
use serde_wasm_bindgen::to_value;

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
    // Replaced deprecated `from_read_ref` with recommended `from_slice`.
    let dictionary_result: Result<Dictionary, _> = from_slice(data);
    match dictionary_result {
        Ok(dictionary) => to_value(&dictionary).map_err(|e| e.into()),
        Err(e) => Err(e.to_string().into()),
    }
}

#[wasm_bindgen]
pub fn load_tokens(data: &[u8]) -> Result<JsValue, JsValue> {
    // Replaced deprecated `from_read_ref` with recommended `from_slice`.
    let tokens_result: Result<HashMap<i32, String>, _> = from_slice(data);
    match tokens_result {
        Ok(tokens) => to_value(&tokens).map_err(|e| e.into()),
        Err(e) => Err(e.to_string().into()),
    }
}
