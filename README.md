# WasmBench: A Dataset of Real-World WebAssembly Binaries

This is a large dataset of **more than 8000 real-world WebAssembly binaries**, collected from **websites, GitHub, NPM, browser extensions**, and other sources.
This collection can be useful to test WebAssembly-related tools, as training data for machine learning, or just to understand better how the language is used in practice.
More details about the dataset, how we collected it, and analysis results of the binaries can be found in the publication **An Empirical Study of Real-World WebAssembly Binaries: Security, Languages, Use Cases** at *The Web Conference 2021 (WWW ’21)*. The paper is available at [https://software-lab.org/publications/www2021.pdf](https://software-lab.org/publications/www2021.pdf).

You can find the full dataset of binaries and metadata under [releases](https://github.com/sola-st/WasmBench/releases).

Specifically, an **archive with all collected binaries** and collected metadata (e.g., where the binary is from, source language, used WebAssembly extensions, etc.) is available here: **https://github.com/sola-st/WasmBench/releases/download/v1.0/all-binaries-metadata.7z**.

A **filtered version of the dataset**, with 8461 unique binaries and their metadata is available here: **https://github.com/sola-st/WasmBench/releases/download/v1.0/filtered-binaries-metadata.7z**.

## Overview

The repository is organized into three directories, roughly based on the phases outlined in the paper:

- `collection/` contains the scripts and intermediate results of the first phase: collecting the raw binaries and some metadata from several sources. There is one subdirectory per source, e.g., `collection/github/` for binaries from repositories on GitHub.
- `filtering-and-analysis/` contains the scripts for filtering the raw dataset (e.g., removing duplicate binaries) and our static analysis tools in Rust and Python.
- `dataset-metadata/` contains an overview and metadata of our final dataset. The binaries themselves are not part of the git repository, but published as a release artifact (due to size restrictions). However, if you are only interested in, for example, the number of unique binaries or where they were found, this metadata should suffice and you do not need to download the full dataset.

Please have a look in each directory for more information on the scripts and data.
(The `dataset/` directory only contains the script for compressing the uploaded archive file, see under releases for the actual download.)

## License

All our own crawling and analysis programs are MIT-licensed. We do not assume ownership or copyright of any of the collected WebAssembly binaries and redistribute them here only for research purposes. All binaries are crawled from public websites and code repositories.
