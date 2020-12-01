# Dataset Metadata

This directory contains the metadata of the collected binaries as (compressed) JSON.
For the full set of binaries, please see the release artifact.

The `all.pretty.json` and `filtered.pretty.json` files are available uncompressed to be easy to access directly.
They contain the full dataset and filtered dataset, respectively.
There is no schema file available, but the rough structure is: the `SHA256(file)` is the key for each entry.
This takes care of duplicates.
For each binary hash, there are some properties related to the binary itself (file size in bytes, whether the binary passes `wasm-validate`, which extensions it uses etc.) and a special property `files` that is a list of (possibly multiple) occurrences of the binary in the raw data (e.g., found in GitHub repo XYZ and on NPM in package ABC.)
The `filtered.list.txt` file is just the list of hashes that remain after filtering.

More metadata is available in the other `*.json.7z` files. You can unpack those by running `7z-uncompress-all.sh`. 
Again, they are indexed by the hash of each binary and contain various information.
Those have been extracted with the programs in the static analysis phase.

- `names.json`: names of functions from imports, exports, or - if available - debug information in the *names* custom section.
- `strings.json`: consecutive ranges of ASCII characters from the *data* section.
- `memory-info.json`: number of memory sections, initial and maximum sizes, counts of memory instructions.
- `unmanaged-stack.json`: index of the inferred stack pointer global variable, number of read and write instructions, number of functions using the stack pointer.