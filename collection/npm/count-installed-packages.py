#!/usr/bin/env python3

import os

def package_names(root_dir):
    for entry in os.listdir(root_dir):
        if entry.startswith('.'):
            continue
        # package namespaces
        elif entry.startswith('@'):
            for package in os.listdir(f'{root_dir}/{entry}'):
                if not entry.startswith('.'):
                    yield f'{entry}/{package}'
        else:
            yield entry


installed_packages = set()
installed_packages.update(package_names('keyword-wasm-WebAssembly/install_merged/node_modules'))
installed_packages.update(package_names('top-ranked/install/node_modules'))
print(sorted(installed_packages))
print(len(installed_packages))
