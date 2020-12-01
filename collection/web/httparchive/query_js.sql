SELECT page, url
FROM `httparchive.response_bodies.2020_06_01_desktop`
WHERE url LIKE '%.js%' AND body LIKE '%WebAssembly%'

