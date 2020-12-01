#!/bin/bash
for package in $(cat ../dependencies-top1k.txt)
do
    echo "Installing $package..."
    mkdir -p "logs/$package"
    npm install $package > "logs/$package/stdout.txt" 2> "logs/$package/stderr.txt"
done
