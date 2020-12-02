# WasmBench: A Dataset of Real-World WebAssembly Binaries

A paper on this benchmark of WebAssembly binaries is currently under submission.

You can find the full dataset of binaries and metadata under [releases](https://github.com/sola-st/WasmBench/releases).

## Overview

The repository is organized into three directories, roughly based on the phases outlined in the paper:

- `collection/` contains the scripts and intermediate results of the first phase: collecting the raw binaries and some metadata from several sources. There is one subdirectory per source, e.g., `collection/github/` for binaries from repositories on GitHub.
- `filtering-and-analysis/` contains the scripts for filtering the raw dataset (e.g., removing duplicate binaries) and our static analysis tools in Rust and Python.
- `dataset-metadata/` contains an overview and metadata of our final dataset. The binaries themselves are not part of the git repository, but published as a release artifact (due to size restrictions). However, if you are only interested in, for example, the number of unique binaries or where they were found, this metadata should suffice and you do not need to download the full dataset.

Please have a look in each directory for more information on the scripts and data.
(The `dataset/` directory only contains the script for compressing the uploaded archive file, see under releases for the actual download.)

## License

All our own crawling and analysis programs are MIT-licensed. We do not assume ownership or copyright of any of the collected WebAssembly binaries and redistribute them here only for research purposes. All binaries are crawled from public websites and code repositories.
