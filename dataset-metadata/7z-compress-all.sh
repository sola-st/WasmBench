#!/bin/bash
for file in *.json
do
    # compress with maximum settings
    # see https://superuser.com/questions/281573/what-are-the-best-options-to-use-when-compressing-files-using-7-zip
    7z a -t7z -m0=lzma -mx=9 -mfb=64 -md=32m -ms=on "$file.7z" "$file"
done
