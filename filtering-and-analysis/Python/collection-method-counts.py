#!/usr/bin/env python3

import json
from collections import Counter
import sys


filename = sys.argv[1]
print(f'Opening {filename}...')
with open(filename) as f:
    data = json.load(f)

# Map from collection method to counts
# Total = repeatedly counting binaries for each occurrence
# Exclusive = only counting a binary if it was only found by this method
total_binaries = Counter()
unique_binaries = Counter()
exclusive_binaries = Counter()
for hash, desc in data.items():
    collection_methods = set()
    for file in desc['files']:
        collection_method = file['collection_method']

        # Align them in the data with the display in the paper
        if collection_method == 'survey':
            collection_method = 'manual'
        if collection_method == 'web/own-crawler':
            collection_method += '/' + file['seed_list']

        collection_methods.add(collection_method)
        total_binaries[collection_method] += 1

    if len(collection_methods) == 1:
        collection_method = list(collection_methods)[0]
        exclusive_binaries[collection_method] += 1

    for collection_method in collection_methods:
        unique_binaries[collection_method] += 1


collection_methods = set(total_binaries.keys()).union(set(unique_binaries.keys())).union(set(exclusive_binaries.keys()))
for c in sorted(collection_methods):
    print(c, total_binaries[c], unique_binaries[c], exclusive_binaries[c])
print('all', sum(total_binaries.values()), len(data))
