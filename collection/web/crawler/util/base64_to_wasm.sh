#!/bin/bash
# (Hacky) script for converting base64 strings collected by the crawler to wasm modules
for file in $1/*.b64.meta; do
    [ -e "$file" ] || continue;
    echo "meta: $file"
    wasm_file=$(grep "file: " $file | cut -d ":" -f 2 | xargs)
    echo "wasm: $wasm_file"
    [ -e "$1/$wasm_file" ] && [ -n "$wasm_file" ] || continue;
    new_name="$(echo "$wasm_file" | sed 's/\./_/g').wasm"
    echo "new: $1/$new_name"
    base64 -d "$1/$wasm_file" > "$1/$new_name" || continue;
    echo "file: $new_name" > "$1/$new_name.meta"
    tail -n +2 "$file" >> "$1/$new_name.meta"
    echo "ok."
done
