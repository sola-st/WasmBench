#!/usr/bin/env python3

import json
from collections import Counter
import matplotlib.pyplot as plt
import statistics
import figure_tools as ft
from print_distribution import print_distribution


print('Loading data...')
index_file = 'filtered.json'
with open(index_file) as f:
    data = json.load(f)
print('Loading names...')
with open('names.json') as f:
    names = json.load(f)
print('  unique:', len(data))
print('  total:', sum(len(desc['files']) for desc in data.values()))
print()


def import_field_name(name: str) -> str:
    return name.split('.', 1)[1]


def is_minified(names: list) -> bool:
    mean_len = statistics.mean(len(name) for name in names)
    return mean_len <= 4


def binary_names(hash):
    for name in names[hash]['imports']:
        yield name
    for name in names[hash]['exports']:
        yield name
    for name in names[hash]['function_names']:
        yield name


# Activate or deactive based on whether you want information for binaries found on the web
ONLY_WEB = False

minification_debug_info = Counter()
custom_sections = Counter()
extensions_counter = Counter()
extensions_combinations_counter = Counter()
total = 0
binaries_pthreads = set()
for hash, desc in data.items():
    if ONLY_WEB and not any('web' in file['collection_method'] for file in desc['files']):
        continue
    total += 1

    if desc['wasm_extensions'] is not None:
        extensions_counter.update(desc['wasm_extensions'])
        extensions_combinations_counter[tuple(sorted(desc['wasm_extensions']))] += 1

    if any('pthread' in name for name in binary_names(hash)):
        binaries_pthreads.add(hash)

    custom_sections_this = set('.debug*' if '.debug' in s else s for s in desc['custom_sections'])
    custom_sections.update(custom_sections_this)

    debug_features = []
    if '.debug*' in custom_sections_this or 'sourceMappingURL' in custom_sections_this:
        debug_features.append('Lines')
    if custom_sections_this & set(('name', '.debug*', 'sourceMappingURL')):
        debug_features.append('Names')
    # if 'name' in custom_sections_this:
    #     debug_features.add('Names')
    # if '.debug*' in custom_sections_this:
    #     debug_features.add('DWARF')
    # if 'sourceMappingURL' in custom_sections_this:
    #     debug_features.add('Source Map')
        
    import_export_names = [name for name in names[hash]['exports']]
    for name in names[hash]['imports']:
        import_export_names.append(import_field_name(name))
    if len(import_export_names) > 10 and is_minified(import_export_names):
        debug_features.append('Minified')

    # DEBUG files with debug info that are still minified!
    # if 'minified' in debug_features and 'name' in debug_features:
    #     print(hash)

    if not debug_features:
        debug_features = 'Normal'
    else:
        debug_features = ' & '.join(debug_features)
    minification_debug_info[debug_features] += 1

print('Custom sections:')
print_distribution(custom_sections, total=total)
print()

print('Minification and debug info combinations:')
print_distribution(minification_debug_info, total=total)
print()

ft.set_font_fira_sans()
ft.set_font_size(18)

minification_debug_info_fig = Counter()
minification_debug_info_fig['Normal'] = minification_debug_info['Normal']
for n, c in minification_debug_info.items():
    if n != 'Normal':
        # if c < 150:
        #     minification_debug_info_fig['Other'] += c
        # else:
        minification_debug_info_fig[n] = c

plt.pie(
    list(minification_debug_info_fig.values()), 
    labels=[f'{name} ({count:,})' for name, count in minification_debug_info_fig.items()],
    autopct='%1.1f%%',
    pctdistance=0.75,
    startangle=90,
)
plt.savefig(f"results/minification{'-web' if ONLY_WEB else ''}-pie.pdf", bbox_inches='tight')

print('Extensions (repeated)')
print_distribution(extensions_counter, total=total)
print()

print('Extensions (combinations)')
print_distribution(extensions_combinations_counter, total=total)
print()

print('pthreads in names of binaries')
print('  binaries:', binaries_pthreads)
print('  count:', len(binaries_pthreads))
