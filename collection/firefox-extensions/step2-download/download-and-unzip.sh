#!/bin/bash
mkdir -p xpi
i=0
for url in $(cat ../addon-urls.txt)
do
    i=$((i+1))
    echo "Downloading $url (#$i)..."
    
    file="xpi/$(basename $url)"
    wget -q -O "$file" "$url"

    dir="unzip/$(basename $url .xpi)/"
    mkdir -p "$dir"
    unzip -q -d "$dir" "$file"
done

# Fix broken permissions in some extensions (directories are not x, so cannot cd into them)
chmod -R +rX unzip/
