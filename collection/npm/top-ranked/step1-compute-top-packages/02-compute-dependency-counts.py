#!/usr/bin/env python3

import json
from collections import Counter
from datetime import datetime

dependencies = Counter()
devDependencies = Counter()
peerDependencies = Counter()
def counters():
    return {
        'dependencies': dict(dependencies.most_common()),
        'devDependencies': dict(devDependencies.most_common()),
        'peerDependencies': dict(peerDependencies.most_common())
    }

i_line = 0
with open('_all_docs?include_docs=true') as f:
    for line in f:
        i_line += 1

        entry_json = None
        try:
            entry_json = json.loads(line.strip('\n').strip(','))
        except json.JSONDecodeError as e:
            print(f'line {i_line}, invalid JSON, {e}')

        if entry_json is not None:
            last_version = {}
            for last_version in entry_json['doc'].get('versions', {}).values():
                continue

            try:
                for dep in last_version.get('dependencies', []) or []:
                    dependencies[dep] += 1
                for dep in last_version.get('devDependencies', []) or []:
                    devDependencies[dep] += 1
                for dep in last_version.get('peerDependencies', []) or []:
                    peerDependencies[dep] += 1
            except TypeError as e:
                print(f'line {i_line}, package {entry_json["id"]}, {e}')

        if i_line % 20000 == 1:
            print(f'{datetime.now()}: done {i_line-1} rows')
            json.dump(counters(), open('dependency-counts.json', 'w'))

json.dump(counters(), open('dependency-counts.json', 'w'))
