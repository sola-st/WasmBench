# Phase 2 and 3: Filtering and Extracting Metadata

This contains the code for combining the results from different collection sources, filtering unrepresentative binaries (e.g., do not validate, generated test files etc.), and static analysis tools and heuristics (e.g., for identifying the used memory allocator).

In `Python/`, you find multiple scripts for (i) combining WebAssembly binaries from the different collection sources (see Phase 1) and deduplicating them based on the SHA256 hash of their contents, (ii) filtering them based on several heuristics and identified projects that are non-representative, and (iii) iteratively extracting and adding metadata to the JSON files (see `dataset-metadata/`).
In `util/` there are also smaller utilities, e.g., functions for nicer figures or printing Python `Counter`s.

In `Rust/`, you find the source code of the static analysis tools for extracting additional information from the WebAssembly binaries.
They extract for example function names, strings from the data section, do unmanaged stack pointer analysis, etc.
The tools are organized into multiple binaries and can be compiled and installed with a recent version of Rust via `cargo build && cargo install --path .`
We use the `wasmparser` library for parsing WebAssembly binaries, which also supports extensions.

Finally, for speeding up the manual analysis of many binaries and finding related ones, we implemented an approximate byte-based n-gram similarity comparison tool.
This is available at https://github.com/hilbigan/ngrm.
