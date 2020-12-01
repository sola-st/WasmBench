#!/bin/bash
for file in *.7z
do
    7z x "$file"
done
