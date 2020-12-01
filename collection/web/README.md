# Collection of binaries from the web

We collected binaries from the web via two main ways: 

- `crawler/`: With our own crawler on three different seed lists and with different exhaustiveness parameters (breadth, depth). This contains our Node.js code that uses a Chrome instance steered with puppeteer and puppeteer cluster. 
- `httparchive/`: Queries of the HTTPArchive summary tables with Google BigQuery.

See the paper for more details and the source code and documentation in those directories.
