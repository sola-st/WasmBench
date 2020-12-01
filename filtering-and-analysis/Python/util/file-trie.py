#!/usr/bin/env python3

import os
import fileinput
import pygtrie

# Read lines from stdin or input file, if given.
# set() to make sure each one is appearing only once
# sorted() to sort them in 'directory order' (DFS traversal)
lines = sorted(set(line.strip() for line in fileinput.input()))
print('total:', len(lines))

# Strip common prefix from all lines
prefix = os.path.commonprefix(lines)
print('prefix:', prefix)
lines = [line[len(prefix):] for line in lines]

trie = pygtrie.StringTrie.fromkeys(lines)

counts = {}
def trie_traverse(path_conv, path, children, directory=True):
    full_path = path_conv(path)
    # HACK Abuse that Python 3 dicts are ordered, so by writing None for the directory, we insert
    # it now into the counts, even though the final count of its subelements is only known later.
    counts[full_path] = None
    if directory:
        count = sum(list(children))
    else:
        count = 1
    counts[full_path] = list(path), count, directory
    return count

# TODO sort trie children by counts
trie.traverse(trie_traverse)

print()
for path, count, directory in counts.values():
    if path == []:
        continue
    if directory:
        # TODO align counts by largest count in children
        print(f"{'    ' * (len(path) - 1)}{path[-1]}/ {count}")
    else:
        print(f"{'    ' * (len(path) - 1)}{path[-1]}")
