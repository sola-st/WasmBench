const fs = require('fs').promises;
const search = require('libnpmsearch');

const QUERY = 'WebAssembly';
// const QUERY = 'wasm';

(async () => {
    let previous_length = -1;
    let results = [];
    do {
        console.log('requesting more...');
        previous_length = results.length;
        results = results.concat(await search(QUERY, { limit: 1000, from: results.length }));
        console.log('previous_length', results.length);
        console.log('results.length', results.length);
    } while (results.length > previous_length);

    console.log(results.map(x => x.name));
    console.log(results.length);
    await fs.writeFile('results.json', JSON.stringify(results, null, 2));
})();
