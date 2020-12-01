#!/usr/bin/env python3

import json
import re
from collections import Counter
import matplotlib.pyplot as plt
import figure_tools as ft


def print_distribution(counter, min_count=0, total=None):
    if total is None:
        total = sum(counter.values())
    for value, count in counter.most_common():
        if count < min_count:
            continue
        percent = count / total
        print(f'  {count:5} ({percent:6.2%}) {value}')


print('Loading data...')
index_file = 'filtered.json'
with open(index_file) as f:
    data = json.load(f)
print('  unique:', len(data))
print('  total:', sum(len(desc['files']) for desc in data.values()))
print('Loading names...')
with open('names.json') as f:
    names = json.load(f)
print('Loading strings...')
with open('strings.json') as f:
    strings = json.load(f)
print()


def print_files_with(hash_predicate):
    files = []
    for hash, desc in data.items():
        if hash_predicate(hash):
            files.extend(file['absolute_path'] for file in desc['files'])
    for file in sorted(files):
        print(file)


def binary_names(hash):
    for name in names[hash]['imports']:
        yield name
    for name in names[hash]['exports']:
        yield name
    for name in names[hash]['function_names']:
        yield name


producers_field_counts = Counter()
producers_languages_counts = Counter()
producers_tools_counts = Counter()
producers_tools_only_name_counts = Counter()
for desc in data.values():
    if desc['producers']:
        producers_field_counts.update(desc['producers'].keys())
        producers_languages_counts.update(desc['producers'].get('language', {}).items())
        producers_tools_counts.update(desc['producers'].get('processed-by', {}).items())
        producers_tools_only_name_counts.update(desc['producers'].get('processed-by', {}).keys())
print('Producer fields')
print_distribution(producers_field_counts, total=len(data))
print('Producer languages')
print_distribution(producers_languages_counts, total=len(data))
print('Producer tools')
print_distribution(producers_tools_counts, total=len(data))
print('Producer tools, without versions')
print_distribution(producers_tools_only_name_counts, total=len(data))
print()

names_unknown = Counter()
strings_unknown = Counter()
extensions_unknown = Counter()
path_components_unknown = Counter()

languages_counts = Counter()
languages_methods_counts = Counter()
languages_methods_combinations_counts = Counter()
for hash, desc in data.items():
    languages = set()
    languages_methods = set()

    # Ground truth: producer section
    if desc['producers']:
        producers_languages = desc['producers'].get('language', {})
        for lang in producers_languages.keys():
            if lang == 'C_plus_plus_14':
                languages.add('C++')
            elif lang == 'C99':
                languages.add('C')
            else:
                languages.add(lang)
            languages_methods.add('producers section')

        producers_tools = desc['producers'].get('processed-by', {})
        for tool in producers_tools.keys():
            # Transformation tools do not tell us anything about the source language...
            if tool in ('walrus', 'Apple LLVM', 'wasm-bindgen'):
                continue
            if tool == 'rustc':
                languages.add('Rust')
            elif tool.startswith('Go'):
                languages.add('Go')
            elif tool == 'clang':
                languages.add('Clang')
            else:
                languages.add(tool)
            languages_methods.add(f'producers section (tool: {tool})')

    # Next best: well known APIs
    # Do not match against cxa_allocate etc., because it matches with Rust programs as well...
    # if any('env.___cxa_throw' == n or 'env.___cxa_allocate_exception' == n for n in binary_names(hash)):
    #     languages.add('C++')
    #     languages_methods.add('names (C++ exceptions)')
    if any(n in ('operator new[](unsigned long)', 'operator delete(void*)', '_ZdaPv', '_ZdlPv', '_Znaj', '_Znwj', '_ZdaPvSt11align_val_t', '_ZnajSt11align_val_t', '_ZnwjSt11align_val_t', '_ZdlPvSt11align_val_t') for n in binary_names(hash)):
        languages.add('C++')
        languages_methods.add('names (C++ new/delete operators)')
    if any('runtime' in name and 'go' in name.lower() for name in binary_names(hash)):
        languages.add('Go')
        languages_methods.add('names (Go runtime)')
    ASSEMBLYSCRIPT_RUNTIME = ('__alloc', '__rtti_base', '__retain', '__collect', '__release')
    if all(name in binary_names(hash) for name in ASSEMBLYSCRIPT_RUNTIME):
        languages.add('AssemblyScript')
        languages_methods.add('names (AssemblyScript runtime)')
    if any(name.startswith('~lib/') for name in binary_names(hash)):
        languages.add('AssemblyScript')
        languages_methods.add('names (AssemblyScript old stdlib)')
    # see https://developers.eos.io/manuals/eosio.cdt/v1.5/group__action/#function-require_auth
    if '_ZN5eosio12require_authERKNS_16permission_levelE' in binary_names(hash):
        languages.add('C++')
        languages_methods.add('names (EOSIO ABI)')
    # see https://github.com/Jacarte/CROW/blob/master/benchmark_programs/rossetta/Readme.md
    if 'polybench_timer_start' in binary_names(hash):
        languages.add('C')
        languages_methods.add('names (polybench/rosettacode of CROW)')
    # see https://github.com/FStarLang/kremlin/search?q=WasmSupport
    if 'WasmSupport.WasmSupport_trap' in binary_names(hash):
        languages.add('FStar')
        languages_methods.add('names (FStar/kremlin import)')
    if 'hyphenate' in binary_names(hash):
        languages.add('AssemblyScript')
        languages_methods.add('names (hyphenate)')
    if any('wbindgen' in name for name in binary_names(hash)):
        languages.add('Rust')
        languages_methods.add('names (wbindgen)')
    if any(re.search('(Kotlin)|(knjs_)|(Konan_)|(kfun:)', name) for name in binary_names(hash)):
        languages.add('Kotlin')
        languages_methods.add('names (Kotlin)')
    if any('emscripten' in name for name in binary_names(hash)):
        languages.add('Emscripten')
        languages_methods.add('names (emscripten)')

    # Strings in data section
    if any(s.startswith('NSt3') or s.startswith('N10__cxx') for s in strings[hash]):
        languages.add('C++')  # Clang standard libc++ mangled type names
        languages_methods.add('strings (libc++ types)')
    if any('Result::unwrap' in s or 'Option::unwrap' in s for s in strings[hash]):
        languages.add('Rust')
        languages_methods.add('strings (std::Result/Option)')
    # see https://github.com/Sable/matwably
    if 'Dimensions of matrices being concatenated are not consistent.' in strings[hash]:
        languages.add('Matlab')
        languages_methods.add('strings (Matlab error)')
    # Do not match this error message, since it matches also for Rust programs compiled to WASI 
    # (likely because they use libc themselves)
    # if 'No space left on device' in strings[hash]:
    #     languages.add('C')
    #     languages_methods.add('strings (WASI/musl libc error')
    # see https://github.com/EOSIO/eosio.cdt/blob/master/libraries/eosiolib/contracts/eosio/multi_index.hpp
    if 'cannot create objects in table of another contract' in strings[hash]:
        languages.add('C++')
        languages_methods.add('strings (EOSIO lib index error)')
    # https://github.com/EOSIO/eosio.cdt/blob/master/libraries/eosiolib/malloc.cpp
    if 'malloc_from_freed was designed to only be called after _heap was completely allocated' in strings[hash]:
        languages.add('C++')
        languages_methods.add('strings (EOSIO lib malloc error)')
    if any('COBOL' in s for s in strings[hash]):
        languages.add('COBOL')
        languages_methods.add('strings (COBOL)')

    path_components = set()
    for file in desc['files']:
        path_components.update(re.split(r'/| |-|_|\.', file['absolute_path']))

    if any('emscripten' == c.lower() for c in path_components):
        languages.add('Emscripten')
        languages_methods.add('path components (emscripten)')
    if any('assemblyscript' == c.lower() for c in path_components):
        languages.add('AssemblyScript')
        languages_methods.add('path components (assemblyscript)')
    if any('fstar' == c.lower() for c in path_components):
        languages.add('FStar')
        languages_methods.add('path components (fstar)')
    if any('turboscript' == c.lower() for c in path_components):
        languages.add('TurboScript')
        languages_methods.add('path components (turboscript)')

    # Specific projects that I manually checked
    # see https://github.com/pepyakin/emchipten
    if 'emchipten' in path_components:
        languages.add('CHIP-8')
        languages_methods.add('path components (emchipten)')
    # see https://github.com/NataliaPavlovic/CPSC411_Compiler
    if 'CPSC411' in path_components:
        languages.add('J--')
        languages_methods.add('path components (CPSC411)')
    if 'CompilerAmy' in path_components or 'amy-compiler' in path_components:
        languages.add('Amy')
        languages_methods.add('path components (amy)')
    if 'ffmpeg' in path_components:
        languages.add('C')
        languages_methods.add('path components (ffmpeg)')
    # Firefox adblocker extensions by gorhill
    if 'adnauseam' in path_components or 'gorhill' in path_components:
        languages.add('wat (manual)')
        languages_methods.add('path components (adnauseam, ublock etc.)')
    # https://github.com/openethereum/wasm-tests
    # if 'openethereum' in path_components:
    #     languages.add('Rust')
    #     languages_methods.add('path components (openethereum)')
    # https://github.com/tree-sitter/tree-sitter/tree/18150a1573b3a97bf6773073e0dcdf0c062c9953/lib/binding_web
    if any('tree-sitter' in file for file['absolute_path'] in desc['files']):
        languages.add('C')
        languages_methods.add('path (tree sitter)')

    # Sibling file extensions, only if everything else failed
    if not languages:
        sibling_extensions = set()
        for file in desc['files']:
            for ext in file['sibling_extensions']:
                sibling_extensions.add(ext)
        if 'cpp' in sibling_extensions or 'cc' in sibling_extensions or 'hpp' in sibling_extensions or 'cxx' in sibling_extensions or 'c++' in sibling_extensions:
            languages.add('C++')
            languages_methods.add('sibling file extension')
        if 'go' in sibling_extensions:
            languages.add('Go')
            languages_methods.add('sibling file extension')
        if 'ts' in sibling_extensions:
            languages.add('AssemblyScript')
            languages_methods.add('sibling file extension')
        if 'rs' in sibling_extensions:
            languages.add('Rust')
            languages_methods.add('sibling file extension')
        if 'c' in sibling_extensions:
            languages.add('C')
            languages_methods.add('sibling file extension')
        # see https://github.com/FantasyInternet/poetry
        if 'poem' in sibling_extensions:
            languages.add('Poem')
            languages_methods.add('sibling file extension')
        # see https://translate.google.com/translate?sl=auto&tl=en&u=https%3A%2F%2Fgithub.com%2Fsfpgmr%2Fmwasm
        if 'mwat' in sibling_extensions:
            languages.add('mwat')
            languages_methods.add('sibling file extension')
        # Most likely from test suites
        if 'wast' in sibling_extensions:
            languages.add('wast')
            languages_methods.add('sibling file extension')

    if not languages and desc['instruction_count'] and desc['instruction_count'] < 100:
        languages.add('too small')
        languages_methods.add('too small')

    # Remove language guesses that are "second tier", i.e., if we have something better:
    SECOND_TIER_GUESS = ('wast', 'Emscripten', 'Clang')
    for guess in SECOND_TIER_GUESS:
        if guess in languages and len(languages) > 1:
            languages.remove(guess)

    if not languages:
        names_unknown.update(binary_names(hash))
        strings_unknown.update(strings[hash])
        extensions_unknown.update(sibling_extensions)
        path_components_unknown.update(path_components)

        # print(hash)
        # for file in desc['files']:
        #     print(file['absolute_path'])

    # Inconsistent predictions!?
    if len(languages) > 1 and languages != set(('C', 'C++')):
        print(hash)
        print('  ', languages)
        print('  ', languages_methods)
        # for file in desc['files']:
        #     print('  ', file['absolute_path'])
        print()

    languages_methods_combinations_counts[tuple(sorted(languages_methods))] += 1
    languages_methods_counts.update(languages_methods)
    languages_counts[tuple(sorted(languages))] += 1

print('Methods (combinations)')
print_distribution(languages_methods_combinations_counts, total=len(data))
print('Methods')
print_distribution(languages_methods_counts, total=len(data))
print('Results')
print_distribution(languages_counts, total=len(data))
print()

# for debugging...

# print('Names, unknown language')
# print_distribution(names_unknown, total=len(data), min_count=20)
# print()

# print('Strings, unknown language')
# print_distribution(strings_unknown, total=len(data), min_count=20)
# print()

# print('Sibling file extensions, unknown language')
# print_distribution(extensions_unknown, total=len(data), min_count=5)
# print()

# print('Path components, unknown language')
# print_distribution(path_components_unknown, total=len(data), min_count=20)
# print()


# Plotting the results
languages_figure = Counter()
for lang, count in languages_counts.most_common():
    lang = [e for e in lang]
    if lang == []:
        lang = 'Unknown'
    if len(lang) == 1:
        lang = lang[0]
    lang == ', '.join(lang)
    if lang == 'Emscripten' or lang == 'Clang' or lang == 'C, C++':
        lang = 'C/C++'
    if lang == 'wast' or lang == 'wat (manual)':
        lang = 'Text format'
    if lang == 'too small':
        lang = '<100 Instructions'
    if count < 100:
        lang = 'Other'
    languages_figure[lang] += count

languages_figure = dict(languages_figure.most_common())

# Move some "special" categories to end
for to_end in ['Other', 'Unknown']:
    to_end_count = languages_figure[to_end]
    del languages_figure[to_end]
    languages_figure[to_end] = to_end_count

# Blue-ish for C and C++, Red-ish for Rust, Grey for stuff that is not so informative
# cmap = plt.get_cmap("tab20c")
# colors = cmap([0, 5, 1, 2, 19, 15, 10, 21, 22])
colors = [
    '#5684c9',  # C++
    '#ec7e1b',  # Rust
    '#5684c9', '#84ace8',  # C/C++
    '#624de9',  # <100 instructions
    '#e9d44d',  # AssemblyScript
    '#2bb2a5',  # Go
    '#eabee4',  # Other
    # '#98c87a',  # Other
    '#cbcbcb',  # Unknown
]

ft.set_font_fira_sans()
ft.set_font_size(18)

plt.pie(
    list(languages_figure.values()), 
    labels=[f'{name} ({count:,})' for name, count in languages_figure.items()],
    autopct='%1.1f%%',
    pctdistance=0.75,
    explode=[0.05, 0, 0.1, 0.1, 0, 0, 0, 0, 0],
    # wedgeprops={'linewidth': 3},
    # rotatelabels=True,
    # startangle=90,
    colors=colors
)
# plt.title('Detected Source Languages')
ft.scale_current_figure(1.1)
plt.savefig('results/languages.pdf', bbox_inches='tight')


methods_figure = Counter()
for methods_tuple, count in languages_methods_combinations_counts.most_common():
    # mash together "submethods", e.g., "strings (emscripten)" -> "strings" and count only once per binary
    methods = set()
    for method in methods_tuple:
        method = method.split('(')[0].strip().title()
        if method == 'Too Small':
            continue
        if method == 'Path Components':
            method = 'Projects'
        methods.add(method)
    for method in methods:
        methods_figure[method] += count


print('Methods for figure:')
print_distribution(methods_figure, total=len(data))

# Move producers section (as most authorative one) to beginning
to_begin = 'Producers Section'
methods_figure_ordered = dict()
methods_figure_ordered[to_begin] = methods_figure[to_begin]
for key, value in methods_figure.items():
    if key != to_begin:
        methods_figure_ordered[key] = value

plt.clf()
plt.pie(
    list(methods_figure_ordered.values()),
    labels=[f'{name} ({count:,})' for name, count in methods_figure_ordered.items()],
    autopct=lambda count: f'{(count/100*sum(methods_figure_ordered.values()))/len(data):.1%}',
    pctdistance=0.6,
    # wedgeprops={'linewidth': 3},
    # rotatelabels=True,
    startangle=90,
    # colors=colors
)
ft.scale_current_figure(0.6)
plt.savefig('results/languages-methods.pdf', bbox_inches='tight')
