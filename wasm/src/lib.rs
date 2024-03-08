use wasm_bindgen::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use rmp_serde::decode::from_read_ref;
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
pub fn load_dictionary(data: &[u8]) -> JsValue {
    let dictionary: Dictionary = from_read_ref(data).unwrap();
    to_value(&dictionary).unwrap()
}

#[wasm_bindgen]
pub fn load_tokens(data: &[u8]) -> JsValue {
    let tokens: HashMap<i32, String> = from_read_ref(data).unwrap();
    to_value(&tokens).unwrap()
}
