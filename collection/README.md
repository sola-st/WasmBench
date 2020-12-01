# Phase 1: Collection of WebAssembly Binaries

There is one subdirectory per collection source.
For a list of all sources and detailed description of the motivation for each, please have a look at the paper.
Except for manually-collected binaries (e.g., found by daily browsing) each directory contains the scripts to 

1. Select which repositories/packages/browser addons etc. to download.
E.g. for NPM, we select (i) the top 1000 depended on packages and (ii) all packages that are found when querying for `wasm` or `WebAssembly`.
Since those results might change over time (and sometimes depend on brittle web-scraping), we also add those lists to the repository.
2. Download/clone/install those artifacts. E.g., for NPM we `npm install` all selected packages (>7000, including transitive dependencies).
Since the number of files and their contents are prohibitively large (>320k files, >150GB), we do not include the raw downloaded files here.
From them we then extract all WebAssembly binaries in our dataset, as described in the paper.
