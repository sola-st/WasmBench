#!/usr/bin/env python3
from glob import glob
import json
from collections import Counter
from scipy.stats import kendalltau

lists = {}

all_repos = Counter()
for path in sorted(glob('results/top*.json')):
    list_id = '-'.join(path.split('-')[1:3])
    print(list_id)

    with open(path) as f:
        data = json.load(f)
    
    lists[list_id] = [d['full_name'] for d in data]

    name_url_stars = [(d['full_name'], d['clone_url'], d['stargazers_count']) for d in data]
    print(name_url_stars[:10])
    for name, url, stars in name_url_stars:
        all_repos[url] = stars

# collect "master list" by merging all input results and sorting by stars
print()
print('all')
print(len(all_repos))
print(all_repos.most_common())

with open('top-repos.txt', 'w') as f:
    for url, count in all_repos.most_common():
        f.write(f'{url}\n')

with open('repos-stars.json', 'w') as f:
    json.dump(dict(all_repos.most_common()), f)

# # compare how similar the lists were
# for id_a, list_a in lists.items():
#     for id_b, list_b in lists.items():
#         tau, p_value = kendalltau(list_a, list_b)
#         print(f'{id_a:20} <> {id_b:20}: {tau:.2}')
