#!/bin/bash
# compress with maximum settings
# see https://superuser.com/questions/281573/what-are-the-best-options-to-use-when-compressing-files-using-7-zip

# for the all dataset, include also the metadata of the filtered ones
7z a -t7z -m0=lzma -mx=9 -mfb=64 -md=32m -ms=on "all-binaries-metadata.7z" "all/" "all.pretty.json" "filtered.pretty.json" "filtered.list.txt"

7z a -t7z -m0=lzma -mx=9 -mfb=64 -md=32m -ms=on "filtered-binaries-metadata.7z" "filtered/" "filtered.pretty.json" "filtered.list.txt"
