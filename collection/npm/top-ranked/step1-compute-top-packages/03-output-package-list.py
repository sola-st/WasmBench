#!/usr/bin/env python3

import json
from collections import Counter

counts = json.load(open('dependency-counts.json'))
dependencies = Counter(counts['dependencies'])
devDependencies = Counter(counts['devDependencies'])
peerDependencies = Counter(counts['peerDependencies'])

print(len(dependencies))
print(len(devDependencies))
print(len(peerDependencies))

print(len([dep for dep, count in dependencies.items() if count >= 1000]))
print(len([dep for dep, count in devDependencies.items() if count >= 1000]))
print(len([dep for dep, count in peerDependencies.items() if count >= 1000]))

print(dependencies.most_common(10))
print(devDependencies.most_common(10))
print(peerDependencies.most_common(10))

print()

nonDevDependencies = Counter()
nonDevDependencies.update(dependencies)
nonDevDependencies.update(peerDependencies)
print(nonDevDependencies.most_common(1000))

with open('dependencies-top1k.txt', 'w') as f:
    for dep, count in dependencies.most_common(1000):
        f.write(f'{dep}\n')

with open('non-dev-dependencies-top1k.txt', 'w') as f:
    for dep, count in nonDevDependencies.most_common(1000):
        f.write(f'{dep}\n')

with open('dev-dependencies-top1k.txt', 'w') as f:
    for dep, count in devDependencies.most_common(1000):
        f.write(f'{dep}\n')

# top = set()
# for dep, c in dependencies.most_common(1000):
#     top.add(dep)
# for dep, c in peerDependencies.most_common(1000):
#     top.add(dep)
# print(len(top))
