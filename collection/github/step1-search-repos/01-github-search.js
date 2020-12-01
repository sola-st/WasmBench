const fs = require('fs').promises;
const { Octokit } = require("@octokit/rest");
const octokit = new Octokit({
    // authenaticate (see Settings -> Developer Settings -> Personal Access Token)
    auth: 'REDACTED'
});

// see https://octokit.github.io/rest.js/v18#search
// and https://docs.github.com/en/free-pro-team@latest/github/searching-for-information-on-github/searching-for-repositories

(async () => {
    const query = 'WebAssembly';
    // const query = 'wasm';
    // const query = 'language:WebAssembly';
    // const query = 'language:wasm';
    // const query = 'topic:WebAssembly';
    // const query = 'topic:wasm';

    // first request, to get beginning of data and amount
    let first_result = await octokit.search.repos({q: query, per_page: 100, sort: 'stars', order: 'desc'});
    let { total_count, items: results } = first_result.data;
    console.log('total_count:', total_count);
    console.log('after first request:', results.length);

    let page = 2;
    while (results.length < total_count) {
        // await new Promise(resolve => setTimeout(resolve, 500));

        let more_result = await octokit.search.repos({q: query, per_page: 100, page, sort: 'stars', order: 'desc'});
        results = results.concat(more_result.data.items);
        console.log(`after more requests (page ${page}):`, results.length);

        await fs.writeFile('results.json', JSON.stringify(results, null, 2));
        page += 1;
    }

    await fs.writeFile('results.json', JSON.stringify(results, null, 2));
})()
