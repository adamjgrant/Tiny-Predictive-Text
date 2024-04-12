(()=>{"use strict";var t={494:(t,n,e)=>{t.exports=e.p+"31d7744fbe7b6cfea014.wasm"}},n={};function e(r){var o=n[r];if(void 0!==o)return o.exports;var i=n[r]={exports:{}};return t[r](i,i.exports,e),i.exports}e.m=t,e.g=function(){if("object"==typeof globalThis)return globalThis;try{return this||new Function("return this")()}catch(t){if("object"==typeof window)return window}}(),e.o=(t,n)=>Object.prototype.hasOwnProperty.call(t,n),(()=>{var t;e.g.importScripts&&(t=e.g.location+"");var n=e.g.document;if(!t&&n&&(n.currentScript&&(t=n.currentScript.src),!t)){var r=n.getElementsByTagName("script");if(r.length)for(var o=r.length-1;o>-1&&(!t||!/^http(s?):/.test(t));)t=r[o--].src}if(!t)throw new Error("Automatic publicPath is not supported in this browser");t=t.replace(/#.*$/,"").replace(/\?.*$/,"").replace(/\/[^\/]+$/,"/"),e.p=t})(),e.b=document.baseURI||self.location.href,(()=>{let t;const n="undefined"!=typeof TextDecoder?new TextDecoder("utf-8",{ignoreBOM:!0,fatal:!0}):{decode:()=>{throw Error("TextDecoder not available")}};"undefined"!=typeof TextDecoder&&n.decode();let r=null;function o(){return null!==r&&0!==r.byteLength||(r=new Uint8Array(t.memory.buffer)),r}function i(t,e){return t>>>=0,n.decode(o().subarray(t,t+e))}const a=new Array(128).fill(void 0);a.push(void 0,null,!0,!1);let c=a.length;function s(t){c===a.length&&a.push(a.length+1);const n=c;return c=a[n],a[n]=t,n}function u(t){return a[t]}function f(t){const n=u(t);return function(t){t<132||(a[t]=c,c=t)}(t),n}let _=0;function l(t,n){const e=n(1*t.length,1)>>>0;return o().set(t,e/1),_=t.length,e}let w=null;function d(){return null!==w&&0!==w.byteLength||(w=new Int32Array(t.memory.buffer)),w}const b="undefined"!=typeof TextEncoder?new TextEncoder("utf-8"):{encode:()=>{throw Error("TextEncoder not available")}},g="function"==typeof b.encodeInto?function(t,n){return b.encodeInto(t,n)}:function(t,n){const e=b.encode(t);return n.set(e),{read:t.length,written:e.length}};async function p(n){if(void 0!==t)return t;void 0===n&&(n=new URL(e(494),e.b));const o=function(){const t={wbg:{}};return t.wbg.__wbindgen_string_new=function(t,n){return s(i(t,n))},t.wbg.__wbindgen_object_drop_ref=function(t){f(t)},t.wbg.__wbindgen_error_new=function(t,n){return s(new Error(i(t,n)))},t.wbg.__wbindgen_is_string=function(t){return"string"==typeof u(t)},t.wbg.__wbindgen_number_new=function(t){return s(t)},t.wbg.__wbindgen_object_clone_ref=function(t){return s(u(t))},t.wbg.__wbg_set_f975102236d3c502=function(t,n,e){u(t)[f(n)]=f(e)},t.wbg.__wbg_new_16b304a2cfa7ff4a=function(){return s(new Array)},t.wbg.__wbg_new_d9bc3a0147634640=function(){return s(new Map)},t.wbg.__wbg_new_72fb9a18b5ae2624=function(){return s(new Object)},t.wbg.__wbg_set_d4638f722068f043=function(t,n,e){u(t)[n>>>0]=f(e)},t.wbg.__wbg_set_8417257aaedc936b=function(t,n,e){return s(u(t).set(u(n),u(e)))},t.wbg.__wbindgen_throw=function(t,n){throw new Error(i(t,n))},t}();("string"==typeof n||"function"==typeof Request&&n instanceof Request||"function"==typeof URL&&n instanceof URL)&&(n=fetch(n));const{instance:a,module:c}=await async function(t,n){if("function"==typeof Response&&t instanceof Response){if("function"==typeof WebAssembly.instantiateStreaming)try{return await WebAssembly.instantiateStreaming(t,n)}catch(n){if("application/wasm"==t.headers.get("Content-Type"))throw n;console.warn("`WebAssembly.instantiateStreaming` failed because your server does not serve wasm with `application/wasm` MIME type. Falling back to `WebAssembly.instantiate` which is slower. Original error:\n",n)}const e=await t.arrayBuffer();return await WebAssembly.instantiate(e,n)}{const e=await WebAssembly.instantiate(t,n);return e instanceof WebAssembly.Instance?{instance:e,module:t}:e}}(await n,o);return function(n,e){return t=n.exports,p.__wbindgen_wasm_module=e,w=null,r=null,t}(a,c)}const y=p;!async function(){await y();const n=await fetch("./dictionary.msgpack"),e=await n.arrayBuffer();!function(n){try{const o=t.__wbindgen_add_to_stack_pointer(-16),i=l(n,t.__wbindgen_malloc),a=_;t.load_dictionary(o,i,a);var e=d()[o/4+0],r=d()[o/4+1];if(d()[o/4+2])throw f(r);return f(e)}finally{t.__wbindgen_add_to_stack_pointer(16)}}(new Uint8Array(e));const r=await fetch("./tokens.msgpack"),i=await r.arrayBuffer();!function(n){try{const o=t.__wbindgen_add_to_stack_pointer(-16),i=l(n,t.__wbindgen_malloc),a=_;t.load_tokens(o,i,a);var e=d()[o/4+0],r=d()[o/4+1];if(d()[o/4+2])throw f(r);return f(e)}finally{t.__wbindgen_add_to_stack_pointer(16)}}(new Uint8Array(i)),window.getPredictiveText=async function(n){try{let e=await function(n){try{const i=t.__wbindgen_add_to_stack_pointer(-16),a=function(t,n,e){if(void 0===e){const e=b.encode(t),r=n(e.length,1)>>>0;return o().subarray(r,r+e.length).set(e),_=e.length,r}let r=t.length,i=n(r,1)>>>0;const a=o();let c=0;for(;c<r;c++){const n=t.charCodeAt(c);if(n>127)break;a[i+c]=n}if(c!==r){0!==c&&(t=t.slice(c)),i=e(i,r,r=c+3*t.length,1)>>>0;const n=o().subarray(i+c,i+r);c+=g(t,n).written,i=e(i,r,c,1)>>>0}return _=c,i}(n,t.__wbindgen_malloc,t.__wbindgen_realloc),c=_;t.get_predictive_text(i,a,c);var e=d()[i/4+0],r=d()[i/4+1];if(d()[i/4+2])throw f(r);return f(e)}finally{t.__wbindgen_add_to_stack_pointer(16)}}(n);return e=(t=>{const n=t.quality;let e=t.prediction;return e=e.map((t=>{let e;const r=t.split(" ").length;return 1===r&&(e=5),2===r&&(e=-1),3===r&&(e=-5),{completion:t,quality:n+e}})),e=e.sort(((t,n)=>n.quality-t.quality)),t.prediction=e,t})(e),e}catch(t){return console.error("Error getting predictive text:",t),[]}};const a=new CustomEvent("tinypredict-ready",{detail:{getPredictiveText:window.getPredictiveText}});window.dispatchEvent(a)}()})()})();