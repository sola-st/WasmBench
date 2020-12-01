#!/usr/bin/env python3

import json
import subprocess
import hashlib
import shutil
import re
import os
import copy
from pathlib import Path
from collections import Counter, defaultdict
import sys


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def wasm_files(root: str, collection_method: str):
    print(f'  {collection_method}...')
    root = Path(root)
    for path in root.glob('**/*.wasm'):
        if path.is_file():
            description = {
                'relative_path': path.relative_to(root),
                'absolute_path': str(path.resolve()),
                'filename': path.name,
                'collection_method': collection_method,
            }

            with path.open('rb') as f:
                bytes = f.read()
                sha256 = hashlib.sha256(bytes).hexdigest()

            yield sha256, description

with open('/home/daniel/wasm-study/github/repos-stars.json') as f:
    GITHUB_STARS = json.load(f)


def npm_package_name(path) -> str:
    first, second = desc['relative_path'].parts[0:2]
    if first.startswith('@'):
        return f'{first}/{second}'
    else:
        return first


# enabled/disabled here means by WABT by default at 2020-10-08
WASM_EXTENSIONS_ENABLED = ['mutable-globals', 'saturating-float-to-int', 'sign-extension', 'multi-value']
WASM_EXTENSIONS_DISABLED = ['exceptions', 'reference-types', 'bulk-memory', 'simd', 'threads', 'tail-call', 'annotations', 'gc', 'memory64']
WASM_EXTENSIONS = WASM_EXTENSIONS_ENABLED + WASM_EXTENSIONS_DISABLED


def check_wasm_extension(path, extension) -> bool:
    commandline = ['wasm-validate', '--ignore-custom-section-errors']

    # Enable all extensions, except for the one given to check.
    for ext in WASM_EXTENSIONS_ENABLED:
        if ext == extension:
            commandline.append(f'--disable-{ext}')
    for ext in WASM_EXTENSIONS_DISABLED:
        if ext != extension:
            commandline.append(f'--enable-{ext}')

    # There are dependencies between extensions, so enabling one silently also enables another extension.
    # Avoid that by disabling both.
    if extension == 'reference-types':
        commandline.remove('--enable-exceptions')
    if extension == 'bulk-memory':
        commandline.remove('--enable-exceptions')
        commandline.remove('--enable-reference-types')

    commandline.append(path)

    # If it doesn't validate with the disabled extension, that one is used by the binary...
    wasm_validate = subprocess.run(commandline, capture_output=True)
    needs_extension = wasm_validate.returncode != 0
    return needs_extension


if os.path.isfile('all.json'):
    eprint('Loading all.json index...')
    with open('all.json') as f:
        all = json.load(f)

    eprint('  total: ', sum(len(desc['files']) for desc in all.values()))
    eprint('  unique:', len(all))
else:
    print('Searching for *.wasm files in all sources...')
    unique_files = defaultdict(list)

    for hash, desc in wasm_files('/home/daniel/wasm-study/github/clone/repos', 'github'):
        repository = '/'.join(desc['relative_path'].parts[0:2])
        desc['repository'] = repository
        stars = GITHUB_STARS[f'https://github.com/{repository}.git']
        desc['stars'] = stars
        unique_files[hash].append(desc)

    for hash, desc in wasm_files('/home/daniel/wasm-study/npm/top-ranked/install/node_modules', 'npm/top'):
        package = npm_package_name(desc['relative_path'])
        desc['package'] = package
        unique_files[hash].append(desc)

    for hash, desc in wasm_files('/home/daniel/wasm-study/npm/keyword-wasm-WebAssembly/install_merged/node_modules', 'npm/wasm'):
        package = npm_package_name(desc['relative_path'])
        desc['package'] = package
        unique_files[hash].append(desc)

    for hash, desc in wasm_files('/home/daniel/wasm-study/wapm/install/wapm_packages', 'wapm'):
        package = '/'.join(desc['relative_path'].parts[0:2]).split('@')[0]
        desc['package'] = package
        unique_files[hash].append(desc)

    for hash, desc in wasm_files('/home/daniel/wasm-study/manual', 'manual'):
        unique_files[hash].append(desc)

    for hash, desc in wasm_files('/home/daniel/wasm-study/survey', 'survey'):
        unique_files[hash].append(desc)

    for hash, desc in wasm_files('/home/daniel/wasm-study/firefox-extensions/download/unzip/', 'firefox-extensions'):
        desc['extension'] = desc['relative_path'].parts[0]
        unique_files[hash].append(desc)

    for hash, desc in wasm_files('/home/daniel/wasm-study/web/httparchive', 'web/httparchive-query'):
        desc['domain'] = desc['relative_path'].parts[0]
        unique_files[hash].append(desc)

    for hash, desc in wasm_files('/home/daniel/wasm-study/web/own-crawler/', 'web/own-crawler'):
        seed_list, wasm_detection, domain = desc['relative_path'].parts[0:3]
        desc['seed_list'] = seed_list
        desc['wasm_detection'] = wasm_detection
        desc['domain'] = domain
        unique_files[hash].append(desc)

    print('  total: ', sum(len(files) for files in unique_files.values()))
    print('  unique:', len(unique_files))

    print('Copying and gathering metadata for unique files...')
    all = {}
    for hash, files in unique_files.items():
        assert files != []
        for file in files:
            # Remove relative_path, only used for extracting repos/packages metadata, redundant with absolute_path.
            del file['relative_path']

            path = Path(file['absolute_path'])

            # Add metadata about individual files, i.e., not only based on binary contents, but also project etc.
            # Sibling extension = same filename, except for a different extension.
            stem = path.stem
            sibling_extensions = []
            for sibling in path.parent.iterdir():
                # filter out broken symlinks before calling samefile (and filtering out directories)
                if sibling.is_file():
                    if not path.samefile(sibling):
                        if sibling.stem == stem:
                            sibling_extension = sibling.name[len(stem):].strip('.')
                            sibling_extensions.append(sibling_extension)
            file['sibling_extensions'] = sibling_extensions

        # Copy unique binaries to all/ directory.
        src = Path(files[0]['absolute_path'])
        dst = f'all/{hash}.wasm'
        shutil.copyfile(src, dst)

        # Gather some more metadata, once per unique file (size, wasm-validate and wasm-objdump outputs...)
        size_bytes = src.stat().st_size

        wasm_validate = subprocess.run(
            ['wasm-validate', '--ignore-custom-section-errors', '--enable-all', dst], capture_output=True)
        if wasm_validate.returncode == 0:
            wasm_validate = True
        else:
            wasm_validate = wasm_validate.stderr.decode('utf-8')

        wasm_validate_no_extensions = subprocess.run(
            ['wasm-validate', '--ignore-custom-section-errors', '--disable-multi-value', '--disable-sign-extension', '--disable-saturating-float-to-int', '--disable-saturating-float-to-int', dst], capture_output=True)
        if wasm_validate_no_extensions.returncode == 0:
            wasm_validate_no_extensions = True
        else:
            wasm_validate_no_extensions = wasm_validate_no_extensions.stderr.decode('utf-8')

        custom_sections = None
        if wasm_validate is True:
            wasm_objdump = subprocess.run(['wasm-objdump', '-h', dst], capture_output=True)
            assert wasm_objdump.returncode == 0
            custom_sections = re.findall('Custom .*"(.*)"', wasm_objdump.stdout.decode('utf-8'))

        wasm_extensions = None
        if wasm_validate is True and wasm_validate_no_extensions != True:
            wasm_extensions = []
            for ext in WASM_EXTENSIONS:
                if check_wasm_extension(dst, ext):
                    wasm_extensions.append(ext)
            assert wasm_extensions != []

        producers = None
        if custom_sections is not None and 'producers' in custom_sections:
            producers = subprocess.run(['parse-producers', dst], capture_output=True)
            assert producers.returncode == 0
            producers = producers.stdout.decode('utf-8')
            producers = json.loads(producers)

        instruction_count = None
        if wasm_validate is True:
            opcodecnt = subprocess.run(['wasm-opcodecnt', '--enable-all', dst], capture_output=True)
            # HACK In some seldom cases, wasm-validate accepts the binary with a zero return code due to
            # errors/warnings only in custom sections, but wasm-opcodecnt complains with an error.
            if opcodecnt.returncode == 0:
                instruction_count = int(re.match(b'Total opcodes: (.*)', opcodecnt.stdout).group(1))
            # else:
            #     print(dst)

        all[hash] = {
            'files': files,
            'size_bytes': size_bytes,
            'wasm_validate': wasm_validate,
            'wasm_validate_no_extensions': wasm_validate_no_extensions,
            'wasm_extensions': wasm_extensions,
            'custom_sections': custom_sections,
            'producers': producers,
            'instruction_count': instruction_count,
        }

    print('Writing metadata file...')
    with open('all.json', 'w') as f:
        json.dump(all, f)
    with open('all.pretty.json', 'w') as f:
        json.dump(all, f, indent=4)
    with open('all.files.txt', 'w') as f:
        for desc in all.values():
            for file in desc['files']:
                f.write(f"{file['absolute_path']}\n")


def remove_files(index: dict, file_predicate):
    # Save copy of index for remembering deleted unique files
    index_old = copy.deepcopy(index)

    # Remove those files where the file matches the predicate
    removed_files = []
    for hash, desc in index.items():
        files = []
        for file in desc['files']:
            if file_predicate(file):
                removed_files.append(file)
            else:
                files.append(file)
        desc['files'] = files

    # Remove unique files with no instances left
    removed_hashes = {}
    for hash, desc in index.items():
        if desc['files'] == []:
            removed_hashes[hash] = index_old[hash]
    for hash in removed_hashes:
        del index[hash]

    return removed_files, removed_hashes


def remove_unique_files(index: dict, desc_predicate):
    # Remove those hashes where the desc matches the predicate
    removed_hashes = {}
    removed_files = []
    for hash, desc in index.items():
        if desc_predicate(desc):
            removed_hashes[hash] = desc
            removed_files.extend(desc['files'])
    for hash in removed_hashes.keys():
        del index[hash]

    return removed_files, removed_hashes


def remove_unique_files_any(index: dict, file_predicate):
    # Remove a unique file, even if just a single instance matches file_predicate
    return remove_unique_files(index, lambda desc: any(file_predicate(file) for file in desc['files']))


eprint('Filtering out "non-representative" files...')
filtered = all

# This only filters out (seemingly) generated/transformed programs from CROW and KTH/slumps repositories, so this is precise.
eprint("  CROW variants: '[' in filename...", end=' ')
removed_files, removed_hashes = remove_files(filtered, lambda file: '[' in file['filename'])
eprint(len(removed_files), len(removed_hashes))

eprint("  KTH superoptimizer outputs...", end=' ')
removed_files, removed_hashes = remove_files(filtered, lambda file: re.search(r'(souper|superoptimizer)(.*)\.opt', file['absolute_path']))
eprint(len(removed_files), len(removed_hashes))

eprint("  AFL generated files: afl_out in path...", end=' ')
removed_files, removed_hashes = remove_unique_files_any(filtered, lambda file: 'afl_out' in file['absolute_path'])
eprint(len(removed_files), len(removed_hashes))

# eprint("  EOSIO...", end=' ')
# removed_files, removed_hashes = remove_files(filtered, lambda file: 'eosio' in file['absolute_path'].lower())
# eprint(len(removed_files), len(removed_hashes))

# eprint("  contract|network|chain...", end=' ')
# removed_files, removed_hashes = remove_files(filtered, lambda file: re.search(r'(contract)|(network)|(chain)', file['absolute_path'].lower()))
# eprint(len(removed_files), len(removed_hashes))

# for file in removed_files:
#     print(file['absolute_path'])

eprint('  Invalid wasm files...', end=' ')
removed_files, removed_hashes = remove_unique_files(filtered, lambda desc: desc['wasm_validate'] != True)
eprint(len(removed_files), len(removed_hashes))

eprint("  Hello world programs: 'hello world' or 'hello wasm' in path...", end=' ')
removed_files, removed_hashes = remove_files(filtered, lambda file: re.search('(hello[\-_ ]?((world)|(wasm)))|(wasm_hello)', file['absolute_path'].lower()))
eprint(len(removed_files), len(removed_hashes))

eprint("  Small test projects: 'wasm_test' or 'test_wasm' in path...", end=' ')
removed_files, removed_hashes = remove_files(filtered, lambda file: re.search('(test_?wasm)|(wasm_?test)|(wasm_add_bg)', file['absolute_path'].lower()))
eprint(len(removed_files), len(removed_hashes))

eprint("  Wasm specification testsuite...", end=' ')
removed_files, removed_hashes = remove_unique_files_any(filtered, lambda file: bool(re.search('wast\.\d+\.wasm', file['absolute_path'])) or 'spec_tests' in file['absolute_path'] or 'spectest' in file['absolute_path'] or 'SpecTestData' in file['absolute_path'] or 'wasm-core-testsuite' in file['absolute_path'] or 'exec/testdata/' in file['absolute_path'] or 'ssvm_unittest' in file['absolute_path'])
eprint(len(removed_files), len(removed_hashes))

eprint("  Testsuite of wasm2lua...", end=' ')
removed_files, removed_hashes = remove_unique_files_any(filtered, lambda file: 'resources/tests/c-testsuite/' in file['absolute_path'] or 'resources/tests/assemblyscript/' in file['absolute_path'])
eprint(len(removed_files), len(removed_hashes))

eprint("  Testsuite of binaryen...", end=' ')
removed_files, removed_hashes = remove_unique_files_any(filtered, lambda file: 'resources/tests/c-testsuite/' in file['absolute_path'] or 'binaryen/test/' in file['absolute_path'])
eprint(len(removed_files), len(removed_hashes))

eprint("  Small programs: <10 instructions...", end=' ')
removed_files, removed_hashes = remove_unique_files(filtered, lambda desc: desc['instruction_count'] is not None and desc['instruction_count'] < 10)
eprint(len(removed_files), len(removed_hashes))

# NOTE seems like a steamhammer?
# eprint("  Test suites: 'test' in path...", end=' ')
# removed_files, removed_hashes = remove_files(filtered, lambda file: 'test' in file['absolute_path'].lower())
# # more fine-grained variant
# # removed_files, removed_hashes = remove_files(filtered, lambda file: (
# #     re.search('(test[\-_ ]?wasm)|(wasm[\-_ ]?test)', file['absolute_path'].lower()) or
# #     'testsuite' in file['absolute_path'].lower() or 
# #     ('wast' in file['absolute_path'].lower() and 'test' in file['absolute_path'].lower())
# # ))
# eprint(len(removed_files), len(removed_hashes))

# eprint("  Unpopular GitHub repos: stars <= 1...", end=' ')
# removed_files, removed_hashes = remove_files(filtered, lambda file: file['collection_method'] == 'github' and file['stars'] <= 1)
# eprint(len(removed_files), len(removed_hashes))

# NOTE This dataset seems to be the input to the fuzzer, not generated files, so I am not sure if it is correct to filter them out?
# eprint("  Fuzzer generated files: 'EOSFuzzer/dataset' in path...", end=' ')
# removed_files, removed_hashes = remove_files(filtered, lambda file: 'EOSFuzzer/dataset' in file['absolute_path'])
# eprint(len(removed_files), len(removed_hashes))

# NOTE also filters out some fuzzers or fuzzy search implemented in WebAssembly
# eprint("  Fuzzer generated files: 'fuzz' in path...", end=' ')
# removed_files, removed_hashes = remove_files(filtered, lambda file: 'fuzz' in file['absolute_path'].lower())
# eprint(len(removed_files), len(removed_hashes))

# NOTE seems like a steamhammer?
# eprint("  Examples: 'example' in path...", end=' ')
# removed_files, removed_hashes = remove_files(filtered, lambda file: 'example' in file['absolute_path'].lower())
# eprint(len(removed_files), len(removed_hashes))

# NOTE why should EOSIO not be representative?
# eprint("  EOSIO smart contracts: 'EOSIO' in path...", end=' ')
# removed_files, removed_hashes = remove_files(filtered, lambda file: 'eosio' in file['absolute_path'].lower())
# eprint(len(removed_files), len(removed_hashes))

# NOTE why, aren't they representative still?
# eprint("  Smart contracts and blockchain: 'contract' in path...", end=' ')
# removed_files, removed_hashes = remove_files(filtered, lambda file: 'contract' in file['absolute_path'].lower())
# eprint(len(removed_files), len(removed_hashes))

# # For debugging last removed files, use with ./collect-index-copy.py | ./file-trie.py > removed.trie.txt
# for file in removed_files:
#     print(file['absolute_path'])
# # for hash, desc in removed_hashes.items():
# #     for file in desc['files']:
# #         print(file['absolute_path'])

eprint('Copying filtered files...')
eprint('  total: ', sum(len(desc['files']) for desc in filtered.values()))
eprint('  unique:', len(filtered))
for hash in filtered.keys():
    src = f'all/{hash}.wasm'
    dst = f'filtered/{hash}.wasm'
    # shutil.copyfile(src, dst)

eprint('Writing filtered metadata file...')
with open('filtered.json', 'w') as f:
    json.dump(filtered, f)
with open('filtered.pretty.json', 'w') as f:
    json.dump(filtered, f, indent=4)
with open('filtered.files.txt', 'w') as f:
    for desc in filtered.values():
        for file in desc['files']:
            f.write(f"{file['absolute_path']}\n")
with open('filtered.trie.txt', 'w') as f:
    trie = subprocess.run(['./file-trie.py', 'filtered.files.txt'], stdout=f)
    assert trie.returncode == 0
