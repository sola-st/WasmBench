const fs = require('fs').promises;
const axios = require('axios');

(async () => {
    let response = await axios.get('https://addons.mozilla.org/api/v4/addons/search/?page_size=50&sort=users&type=extension&lang=en');
    let count = response.data.count;
    let results = response.data.results;
    let next = response.data.next;
    console.log('total count:', count);
    console.log('after first request:', results.length);

    while (results.length < count) {
        response = await axios.get(next);
        next = response.data.next;
        results = results.concat(response.data.results);
        console.log(`after more requests:`, results.length);

        await fs.writeFile('results.json', JSON.stringify(results));
    }

    await fs.writeFile('results.json', JSON.stringify(results));
})()
