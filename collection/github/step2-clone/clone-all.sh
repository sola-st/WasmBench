#!/bin/bash
i=0
for repo in $(cat ../repos-to-clone.txt)
do
    i=$((i+1))
    echo "Cloning $repo (#$i)..."

    user=$(echo "$repo" | cut -d'/' -f4)
    mkdir -p "repos/$user/"
    pushd "repos/$user/" > /dev/null
    
    git clone --depth 1 "$repo"
    
    popd > /dev/null
done
