use wasm_bindgen::prelude::*;

#[wasm_bindgen]
pub fn greet() {
    alert("Hello, wasm!");
}

#[wasm_bindgen]
extern "C" {
    pub fn alert(s: &str);
}

