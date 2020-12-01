The sql files query_wasm_1.sql, query_wasm_2.sql contain the queries we used to
collect WebAssembly files from Google BigQuery. We also provide the resulting
csv files which we directly downloaded binaries from 
(query_wasm_results-\*.csv).

The file query_js.sql contains the query used to retrieve URLs to JavaScript 
files using the `WebAssembly` keyword. The corresponding output -- after
slight modification for easier processing -- can be found in 
js_urls_httparchive.csv.

