#!/bin/bash
for package in $(cat ../packages-wasm-WebAssembly.txt)
do
    echo "Installing $package..."
    mkdir -p "logs/$package"
    # --force to download resource, even if a local copy exists (helps fixing npm errors)
    npm install --force $package > "logs/$package/stdout.txt" 2> "logs/$package/stderr.txt"
done
