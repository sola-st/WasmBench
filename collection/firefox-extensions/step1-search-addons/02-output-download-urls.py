#!/usr/bin/env python3
import json

with open('results.json') as f:
    data = json.load(f)

print(len(set(d['id'] for d in data)))
# print(json.dumps(data[0]))

addon_urls = [d['current_version']['files'][0]['url'] for d in data]
print(len(addon_urls))

with open('addon-urls.txt', 'w') as f:
    for url in addon_urls:
        f.write(f'{url}\n')
