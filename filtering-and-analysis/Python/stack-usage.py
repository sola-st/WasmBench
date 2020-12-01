#!/usr/bin/env python3

import json
from collections import Counter
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import figure_tools as ft
from print_distribution import print_distribution


print('Loading data...')
index_file = 'filtered.json'
with open(index_file) as f:
    data = json.load(f)

print('Loading stack-pointers...')
with open('unmanaged-stack.json') as f:
    sp_info = json.load(f)

print('  unique:', len(data))
print('  total:', sum(len(desc['files']) for desc in data.values()))
print()


def print_files_with(hash_predicate):
    files = []
    for hash, desc in data.items():
        if hash_predicate(hash):
            files.extend(file['absolute_path'] for file in desc['files'])
    for file in sorted(files):
        print(file)


stack_pointers = Counter()
sp_usage_by_function = []
read_write_proportion = []
for hash, desc in data.items():
    sptr = sp_info[hash]['stack_pointer_inferred']
    # if type(sp) is not str and sp != 0:
    #     print(hash, 'sp:', sp)
    #     for file in desc['files']:
    #         print('  ', file['absolute_path'])
    stack_pointers[str(sptr)] += 1

    # if type(sp) is int:
    #     reads, writes = sp_info[hash]['stack_pointer_reads'], sp_info[hash]['stack_pointer_writes']
    #     if reads is None or writes is None:
    #         print(hash)
    #     else:
    #         read_write_proportion.append((reads, writes, sp_info[hash]['functions_all_local']))

    sp_proportion = sp_info[hash]['functions_using_stack_pointer'] / (sp_info[hash]['functions_all_local'] or 1)
    if type(sptr) is int:
        sp_usage_by_function.append(sp_proportion)

print('Stack pointer inferred:')
print_distribution(stack_pointers)

ft.set_font_fira_sans()
ft.set_font_size(18)

sp_pie_figure = {}
sp_pie_figure['Stack pointer:\n global 0'] = stack_pointers['0']
sp_pie_figure['Stack pointer: others '] = sum(c for sp, c in stack_pointers.items() if sp.isnumeric() and sp != '0')
sp_pie_figure['No memory'] = stack_pointers['no local or imported memory']
sp_pie_figure['No mut i32 global'] = stack_pointers['no mutable i32 global']
sp_pie_figure['Not enough accesses'] = stack_pointers['not enough uses of all candidate pointers']

plt.pie(
    list(sp_pie_figure.values()), 
    labels=[f'{name} ({count:,})' for name, count in sp_pie_figure.items()],
    autopct='%1.1f%%',
    pctdistance=0.75,
    startangle=90,
)
plt.savefig('results/stack-pointer-pie.pdf', bbox_inches='tight')


print('Stack pointer by functions:')
df = pd.DataFrame(sorted(sp_usage_by_function))
print(df.describe())

plt.clf()

x = df[0] * 100
y = np.arange(len(df)) / len(df) * 100

plt.step(x, y, where="post")

plt.gca().set_yticks(ticks=np.arange(0, 101, 20))
plt.gca().set_yticks(ticks=np.arange(0, 101, 10), minor=True)
plt.gca().set_xticks(ticks=np.arange(0, 101, 20))
plt.gca().set_xticks(ticks=np.arange(0, 101, 10), minor=True)
plt.gca().yaxis.set_major_formatter(mpl.ticker.FormatStrFormatter('%d%%'))
plt.gca().xaxis.set_major_formatter(mpl.ticker.FormatStrFormatter('%d%%'))
plt.grid(True, which="major", axis="y", color=".85", ls="-")
plt.grid(True, which="minor", axis="y", color=".85", ls=":")
plt.grid(True, which="major", axis="x", color=".85", ls="-")
plt.grid(True, which="minor", axis="x", color=".85", ls=":")

plt.xlabel("Functions Using the Unmanaged Stack")
plt.ylabel("Percentile of Binaries")

plt.tight_layout()
ft.scale_current_figure(0.9)
plt.savefig("results/stack-pointer-functions-cdf.pdf")
