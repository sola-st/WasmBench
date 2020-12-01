SELECT DISTINCT(url) FROM `httparchive.summary_requests.2020_04_01_desktop` 
WHERE (mimeType = 'application/wasm' OR mimeType = 'application/octet-stream' OR mimeType = "application/wasm;charset=UTF-8") AND url LIKE "%.wasm%"
