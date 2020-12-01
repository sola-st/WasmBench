#!/usr/bin/env python3
from collections import Counter, defaultdict
from id_tokenizer import tokenize
import json


def print_distribution(counter, min_count=0, total=None):
    if total is None:
        total = sum(counter.values())
    for value, count in counter.most_common():
        if count < min_count:
            continue
        percent = count / total
        print(f'  {count:5} ({percent:6.2%}) {value}')


def contains_all_tokens_lower(import_name: str, must_match: str) -> bool:
    import_tokens = set(t.lower() for t in tokenize(import_name))
    must_match_tokens = set(t.lower() for t in tokenize(must_match))
    return must_match_tokens.issubset(import_tokens)


print('Loading data...')
with open('filtered.json') as f:
    data = json.load(f)
print('  unique:', len(data))
print('Loading names...')
with open('names.json') as f:
    names = json.load(f)
print()

print('Common imports:')
tokens_counter = Counter()
imports_counter = Counter()
for hash in data.keys():
    imports = names[hash]['imports']
    import_tokens_binary_lower = set()
    for import_name in imports:
        import_tokens = tokenize(import_name)
        # take only tokens once per binary, such that max_count == len(data)
        for t in import_tokens:
            if len(t) > 1:
                import_tokens_binary_lower.add(t.lower())
        # imports_counter[tuple(import_tokens)] += 1
        # if any(w in [t.lower() for t in import_tokens] for w in relevant_words):
        # if any(w in import_name.lower() for w in relevant_words):
        imports_counter[import_name] += 1
    tokens_counter.update(import_tokens_binary_lower)

print_distribution(imports_counter, min_count=300, total=len(data))
print()

print('Common tokens (lowercased, at most once per binary):')
print_distribution(tokens_counter, min_count=500, total=len(data))
print()

matching_imports = []  # list of tuples: (match_category, match_word, import_name, binary_hash)
for hash, desc in data.items():
    for import_name in names[hash]['imports']:

        match_category = "Code execution"
        match_word = "eval"
        # Exclude AUTOCAD binary with 'AcDb' substring and WebGL eval with 'gl' substring since those are not JS eval
        if contains_all_tokens_lower(import_name, match_word) and 'AcDb' not in import_name and 'gl' not in import_name:
            matching_imports.append((match_category, match_word, import_name, hash))
        match_word = "exec"
        if contains_all_tokens_lower(import_name, match_word):
            matching_imports.append((match_category, match_word, import_name, hash))
        match_word = "execve"
        if contains_all_tokens_lower(import_name, match_word):
            matching_imports.append((match_category, match_word, import_name, hash))
        match_word = "emscripten_run_script"
        if contains_all_tokens_lower(import_name, match_word):
            matching_imports.append((match_category, match_word, import_name, hash))

        match_category = "Network"
        match_word = "xhr"
        if contains_all_tokens_lower(import_name, match_word):
            matching_imports.append((match_category, match_word, import_name, hash))
        match_word = "fetch"
        if contains_all_tokens_lower(import_name, match_word) and 'atomic' not in import_name:
            matching_imports.append((match_category, match_word, import_name, hash))
        match_word = "request"
        if contains_all_tokens_lower(import_name, match_word) and 'pointerlock' not in import_name and 'fullscreen' not in import_name and 'Animation' not in import_name:
            matching_imports.append((match_category, match_word, import_name, hash))
        match_word = "http"
        if contains_all_tokens_lower(import_name, match_word):
            matching_imports.append((match_category, match_word, import_name, hash))

        match_category = "File I/O"
        match_word = "file"
        if contains_all_tokens_lower(import_name, match_word):
            matching_imports.append((match_category, match_word, import_name, hash))
        match_word = "fd"
        # Avoid false matches with hashes in cargo_web_snippet and extjs
        if contains_all_tokens_lower(import_name, match_word) and 'cargo_web_snippet' not in import_name and 'extjs' not in import_name:
            matching_imports.append((match_category, match_word, import_name, hash))
        match_word = "path"
        if contains_all_tokens_lower(import_name, match_word) and 'Canvas' not in import_name:
            matching_imports.append((match_category, match_word, import_name, hash))

        match_category = "DOM interaction"
        match_word = "document"
        if contains_all_tokens_lower(import_name, match_word) and 'canvas' not in import_name.lower() and 'css' not in import_name:
            matching_imports.append((match_category, match_word, import_name, hash))
        match_word = "html"
        if contains_all_tokens_lower(import_name, match_word) and 'canvas' not in import_name.lower() and 'css' not in import_name:
            matching_imports.append((match_category, match_word, import_name, hash))
        match_word = "body"
        if contains_all_tokens_lower(import_name, match_word) and 'canvas' not in import_name.lower() and 'css' not in import_name:
            matching_imports.append((match_category, match_word, import_name, hash))
        match_word = "element"
        if contains_all_tokens_lower(import_name, match_word) and 'canvas' not in import_name.lower() and 'css' not in import_name:
            matching_imports.append((match_category, match_word, import_name, hash))

        match_category = "Dynamic linking"
        match_word = "dlopen"
        if match_word in import_name:
            matching_imports.append((match_category, match_word, import_name, hash))
        match_word = "dlsym"
        if match_word in import_name:
            matching_imports.append((match_category, match_word, import_name, hash))
        match_word = "dlclose"
        if match_word in import_name:
            matching_imports.append((match_category, match_word, import_name, hash))

        match_category = "Syscall interfaces"
        match_word = "faasm"
        if match_word in import_name:
            matching_imports.append((match_category, match_word, import_name, hash))
        match_word = "syscall"
        if match_word in import_name:
            matching_imports.append((match_category, match_word, import_name, hash))
        match_word = "wasi"
        if match_word in import_name:
            matching_imports.append((match_category, match_word, import_name, hash))
        match_word = "widl"
        if match_word in import_name:
            matching_imports.append((match_category, match_word, import_name, hash))
        match_word = "eosio"
        if match_word in import_name:
            matching_imports.append((match_category, match_word, import_name, hash))
        match_word = "emscripten"
        if match_word in import_name:
            matching_imports.append((match_category, match_word, import_name, hash))
        match_word = "wbg"
        if match_word in import_name:
            matching_imports.append((match_category, match_word, import_name, hash))

# DEBUG for inspecting matched imports
inspected_category = 'File I/O'
print(f'matching import names for category {inspected_category}:')
print(Counter(import_name for category, word, import_name, binary_hash in matching_imports if category == inspected_category))
print()

categories_import_counts = Counter()
categories_to_binaries = defaultdict(set)
for category, word, name, hash in matching_imports:
    categories_import_counts[category] += 1
    categories_to_binaries[category].add(hash)
category_binary_counts = Counter({category: len(binaries) for category, binaries in categories_to_binaries.items()})

print('categories import counts:')
total_imports = sum(len(names[hash]['imports']) for hash in data.keys())
print('total imports:', total_imports)
print('matching imports total:', len(matching_imports))
print_distribution(categories_import_counts, total=total_imports)
print()

print('categories with binaries matching:')
print_distribution(category_binary_counts, total=len(data))

any_category_import_count = len(set((hash, import_name) for category, word, import_name, hash in matching_imports if category != "Syscall interfaces"))
# any_category_import_count = sum(count for category, count in categories_import_counts.items() if category != "Syscall interfaces")
print('imports with at least one (except generic syscalls)', any_category_import_count)

any_category_binaries = set()
for category, binaries in categories_to_binaries.items():
    if category != "Syscall interfaces":
        for hash in binaries:
            any_category_binaries.add(hash)
any_category_binary_count = len(any_category_binaries)
print('binaries with at least one (except generic syscalls)', any_category_binary_count, f'{any_category_binary_count/len(data):.2%}')
