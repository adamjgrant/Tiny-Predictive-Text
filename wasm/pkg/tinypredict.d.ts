/* tslint:disable */
/* eslint-disable */
/**
* @param {Uint8Array} data
* @returns {any}
*/
export function load_dictionary(data: Uint8Array): any;
/**
* @param {Uint8Array} data
* @returns {any}
*/
export function load_tokens(data: Uint8Array): any;
/**
* @param {string} input
* @returns {any}
*/
export function get_predictive_text(input: string): any;

export type InitInput = RequestInfo | URL | Response | BufferSource | WebAssembly.Module;

export interface InitOutput {
  readonly memory: WebAssembly.Memory;
  readonly load_dictionary: (a: number, b: number, c: number) => void;
  readonly load_tokens: (a: number, b: number, c: number) => void;
  readonly get_predictive_text: (a: number, b: number, c: number) => void;
  readonly __wbindgen_add_to_stack_pointer: (a: number) => number;
  readonly __wbindgen_malloc: (a: number, b: number) => number;
  readonly __wbindgen_realloc: (a: number, b: number, c: number, d: number) => number;
}

export type SyncInitInput = BufferSource | WebAssembly.Module;
/**
* Instantiates the given `module`, which can either be bytes or
* a precompiled `WebAssembly.Module`.
*
* @param {SyncInitInput} module
*
* @returns {InitOutput}
*/
export function initSync(module: SyncInitInput): InitOutput;

/**
* If `module_or_path` is {RequestInfo} or {URL}, makes a request and
* for everything else, calls `WebAssembly.instantiate` directly.
*
* @param {InitInput | Promise<InitInput>} module_or_path
*
* @returns {Promise<InitOutput>}
*/
export default function __wbg_init (module_or_path?: InitInput | Promise<InitInput>): Promise<InitOutput>;
