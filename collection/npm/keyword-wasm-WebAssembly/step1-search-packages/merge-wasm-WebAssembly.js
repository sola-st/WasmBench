const fs = require('fs');
const results_wasm = JSON.parse(fs.readFileSync('results-wasm.json', 'utf8'));
const results_WebAssembly = JSON.parse(fs.readFileSync('results-WebAssembly.json', 'utf8'));
console.log(results_wasm.length);
console.log(results_WebAssembly.length);

let results = new Set(results_wasm.map(x => x.name));
results_WebAssembly.map(x => x.name).forEach(x => results.add(x))
console.log(results.size)
fs.writeFileSync('results-list.txt', Array.from(results).join('\n'));
