#!/usr/bin/env python3

import json
import re
from collections import Counter, defaultdict
import matplotlib.pyplot as plt

import figure_tools as ft
from print_distribution import print_distribution

print('Loading data...')
with open('filtered.json') as f:
    data = json.load(f)

print('Loading memory info...')
with open('memory-info.json') as f:
    mem_info = json.load(f)

print('Loading names...')
with open('names.json') as f:
    names = json.load(f)

print('Loading strings...')
with open('strings.json') as f:
    strings = json.load(f)

print('  unique:', len(data))
print('  total:', sum(len(desc['files']) for desc in data.values()))
print()


def print_files(hash):
    print(hash)
    for file in data[hash]['files']:
        print('  ', file['absolute_path'])


def names_all(hash):
    for name in names[hash]['imports']:
        yield name
    for name in names[hash]['exports']:
        yield name
    for name in names[hash]['function_names']:
        yield name

ALLOC_REGEX = re.compile(r'(alloc)|(free)|(new)|(delete)|(heap)|(grow)')
DLMALLOC_REGEX = re.compile(r'dl((malloc)|(free)|(calloc)|(realloc)|(memalign)|(p?valloc))')
alloc_names = Counter()
alloc_strings = Counter()
memory_usage = Counter()
allocators_detected = Counter()
memory_initial_sizes = []
for hash, desc in data.items():

    # Step 1: generic memory features
    if mem_info[hash]['memory_count'] == 0:
        memory_usage['No memory'] += 1
        allocators_detected['No memory'] += 1
        continue
    if mem_info[hash]['memory_ops_count'] == 0:
        memory_usage['No loads/stores'] += 1
        allocators_detected['No loads/stores'] += 1
        continue

    mem_features = set()
    alloc_features = set()

    mem_grow = mem_info[hash]['memory_grow_count']
    mem_features.add(f'memory.grow: {mem_grow}')
    # if mem_grow > 0:
    #     mem_features.add('memory.grow')
    mem_size = mem_info[hash]['memory_size_count']
    mem_features.add(f'memory.size: {mem_size}')
    # if mem_size > 0:
    #     mem_features.add('memory.size')

    mem_count = mem_info[hash]['memory_count']
    mem_can_grow_count = len(mem_info[hash]['memories_upper_limit'])
    assert mem_count == mem_can_grow_count, hash

    mem_can_grow = not all(mem_info[hash]['memories_upper_limit'])
    if mem_can_grow:
        mem_features.add('memory can grow')
    else:
        mem_features.add('memory fixed size')

    # Step 2: specific allocators

    # wee_alloc
    wee_alloc_count = sum('wee_alloc' in name for name in names_all(hash))
    if wee_alloc_count > 0:
        alloc_features.add('wee_alloc')
    wee_alloc_count = sum('wee_alloc' in s for s in strings[hash])
    if wee_alloc_count > 0:
        alloc_features.add('wee_alloc')

    # emmalloc
    emmalloc_count = sum('emmalloc' in name for name in names_all(hash))
    if emmalloc_count > 0:
        alloc_features.add('emmalloc')
    emmalloc_count = sum('emmalloc' in s for s in strings[hash])
    if emmalloc_count > 0:
        alloc_features.add('emmalloc')

    # EOSIO
    eosio_1 = mem_grow == 2 and mem_size == 6
    if eosio_1:
        alloc_features.add('EOSIO malloc')
    # https://github.com/EOSIO/eosio.cdt/blob/796ff8bee9a0fc864f665a0a4d018e0ff18ac383/libraries/eosiolib/malloc.cpp#L289
    # not present for graphenelib.cpp, because commented out 
    # https://github.com/gxchain/gxb-core/blob/b0e09661f690fd8b65b71552fb937e622b625df8/contracts/graphenelib/graphenelib.cpp#L285
    # but first feature is still reliable
    eosio_2 = any('malloc_from_freed was designed to only be called after _heap was completely allocated' in s for s in strings[hash])
    if eosio_2:
        alloc_features.add('EOSIO malloc')
    # https://github.com/EOSIO/eosio.cdt/blob/796ff8bee9a0fc864f665a0a4d018e0ff18ac383/libraries/eosiolib/simple_malloc.cpp#L49
    if 'failed to allocate pages' in strings[hash]:
        alloc_features.add('EOSIO simple_malloc')

    # Go
    # https://golang.org/src/runtime/malloc.go
    if any('runtime.mallocgc' in name for name in names_all(hash)):
        alloc_features.add('Go malloc')

    # Abseil
    # https://github.com/abseil/abseil-cpp/blob/b86fff162e15ad8ee534c25e58bf522330e8376d/absl/base/internal/low_level_alloc.cc#L438
    if any('LowLevelAlloc arithmetic overflow' in s for s in strings[hash]):
        alloc_features.add('Abseil LowLevelAlloc')

    # AssemblyScript __alloc, __retain etc.
    # https://www.assemblyscript.org/runtime.html#interface
    for w in ['__retain', '__alloc', '__collect', '__release']:
        if any(name.startswith(w) for name in names_all(hash)):
            # alloc_features.add(f'AssemblyScript: {w}')
            alloc_features.add('AssemblyScript alloc')

    # Boehm GC
    if any('GC Warning: Repeated allocation of very large block' in s for s in strings[hash]):
        alloc_features.add('Boehm GC')

    # gperftools
    # https://github.com/gperftools/gperftools/blob/f47a52ce85c3d8d559aaae7b7a426c359fbca225/src/malloc_hook.cc
    if any('MallocHook::RemovePreMmapHook' in s for s in strings[hash]):
        alloc_features.add('gperftools')

    # dlmalloc (Rust and emscripten)
    # see https://github.com/emscripten-core/emscripten/blob/master/system/lib/dlmalloc.c
    if any(DLMALLOC_REGEX.search(name) for name in names_all(hash)):
        alloc_features.add('dlmalloc')
    if any('emscripten_builtin_malloc' in name for name in names_all(hash)):
        alloc_features.add('dlmalloc')
    # https://github.com/emscripten-core/emscripten/blob/c8c05ed9b72d8a7871cc9cc2930989fd703511fb/system/lib/dlmalloc.c#L3608
    if any('max system bytes' in s for s in strings[hash]):
        alloc_features.add('dlmalloc')

    # low-level features, not much info there...
    if any('emscripten' in file['absolute_path'] for file in desc['files']) or any('emscripten' in name for name in names_all(hash)) or any('emscripten' in s for s in strings[hash]):
        alloc_features.add('emscripten')

    if not alloc_features and any('malloc' in name or 'free' in name for name in names_all(hash)):
        alloc_features.add('malloc/free')

    # alloc_features.add(f'grow{mem_grow}|size{mem_size}')
    
    # Exploration: check strings and names related to allocators that were not yet detected
    if not alloc_features:
        alloc_names.update(name for name in names_all(hash) if ALLOC_REGEX.search(name))
        alloc_strings.update(s for s in strings[hash] if ALLOC_REGEX.search(s))

    if not alloc_features:
        memory_initial_sizes.extend(pages * 1024 * 64 for pages in mem_info[hash]['memories_initial_size'])

    memory_usage[str(sorted(mem_features))] += 1
    allocators_detected[str(sorted(alloc_features))] += 1

# DEBUG for development and understanding
# print('Allocation-related names')
# print_distribution(alloc_names, min_count=20)
# print()

# print('Allocation-related strings')
# print_distribution(alloc_strings, min_count=20)
# print()

print('Memory features')
print_distribution(memory_usage)
print()

print('Detected allocators')
print_distribution(allocators_detected)
print()

# plt.hist(memory_initial_sizes, bins=10000)
# plt.savefig('results/memory-sizes-initial.pdf')
print(Counter(memory_initial_sizes).most_common(100))

ft.set_font_fira_sans()
ft.set_font_size(18)

# since binaries contain more than one allocator, the sum goes > 100%
alloc_figure = {}

# Default allocators
alloc_figure['dlmalloc'] = sum(count for alloc, count in allocators_detected.items() if 'dlmalloc' in alloc)
alloc_figure['emscripten'] = allocators_detected["['emscripten']"]
alloc_figure['Go malloc'] = allocators_detected["['Go malloc']"]
alloc_figure['AssemblyScript alloc'] = allocators_detected["['AssemblyScript alloc']"]

# Custom allocators, usually for code size reasons, not hardened
alloc_figure['eosio malloc'] = allocators_detected["['EOSIO malloc']"]
alloc_figure['eosio simple_malloc'] = allocators_detected["['EOSIO simple_malloc']"]
alloc_figure['Boehm GC'] = allocators_detected["['Boehm GC', 'emscripten']"]
alloc_figure['wee_alloc'] = sum(count for alloc, count in allocators_detected.items() if 'wee_alloc' in alloc)
alloc_figure['emmalloc'] = sum(count for alloc, count in allocators_detected.items() if 'emmalloc' in alloc)
alloc_figure['Others'] = sum(count for alloc, count in allocators_detected.items() if 'Abseil' in alloc or 'gperftools' in alloc)

# Other
alloc_figure['No memory'] = allocators_detected["No memory"]
alloc_figure['No loads/stores'] = allocators_detected["No loads/stores"]
alloc_figure['Unknown'] = allocators_detected["[]"] + allocators_detected["['malloc/free']"]

# sp_pie_figure['Stack pointer: others '] = sum(c for sp, c in stack_pointers.items() if sp.isnumeric() and sp != '0')
# sp_pie_figure['No memory'] = stack_pointers['no local or imported memory']
# sp_pie_figure['No mut i32 global'] = stack_pointers['no mutable i32 global']
# sp_pie_figure['Not enough accesses'] = stack_pointers['not enough uses of all candidate pointers']

plt.pie(
    list(alloc_figure.values()), 
    labels=[f'{name} ({count:,})' for name, count in alloc_figure.items()],
    autopct='%1.1f%%',
    pctdistance=0.75,
    startangle=90,
)
plt.savefig('results/allocator-pie.pdf', bbox_inches='tight')
