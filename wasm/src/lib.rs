use wasm_bindgen::prelude::*;
use serde::{Deserialize, Serialize};
use rmp_serde::decode::from_read_ref;

#[derive(Serialize, Deserialize)]
struct Dictionary {
    // Adjust this to match the structure of your MessagePack data
    key: String,
    value: i32,
}

#[derive(Serialize, Deserialize)]
struct Token {
    // Similarly, adjust to match your data structure
    token: String,
}

#[wasm_bindgen]
pub fn load_dictionary(data: &[u8]) -> JsValue {
    let dictionary: Dictionary = from_read_ref(data).unwrap();
    JsValue::from_serde(&dictionary).unwrap()
}

#[wasm_bindgen]
pub fn load_tokens(data: &[u8]) -> JsValue {
    let tokens: Token = from_read_ref(data).unwrap();
    JsValue::from_serde(&tokens).unwrap()
}