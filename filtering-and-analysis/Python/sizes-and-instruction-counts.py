#!/usr/bin/env python3

import json
from collections import Counter
from scipy import stats
import figure_tools as ft
import pandas as pd
from matplotlib import pyplot as plt
import sys
import numpy as np


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


with open('filtered.json') as f:
    data = json.load(f)

sizes = [desc['size_bytes'] for desc in data.values()]
print(len(sizes), min(sizes), max(sizes))
# print('max', max(enumerate(items), key=lambda x: x[1]),)

instruction_counts = [desc['instruction_count'] for desc in data.values() if desc['instruction_count'] is not None]
print(len(instruction_counts), min(instruction_counts), max(instruction_counts))

ft.set_font_fira_sans()
ft.set_font_size(20)

# grid lines behind bar char, see https://stackoverflow.com/questions/1726391/matplotlib-draw-grid-lines-behind-other-graph-elements
plt.rcParams['axes.axisbelow'] = True

plt.grid(True, which="major", axis="y", color=".85", ls="-")
plt.grid(True, which="major", axis="x", color=".85", ls="-")
# plt.grid(True, which="minor", axis="y", color=".85", ls=":")

df_instruction_counts = pd.DataFrame(sorted(instruction_counts))
print(df_instruction_counts)
print('statistics for instruction counts')
print(df_instruction_counts.describe(percentiles=[0.1,0.2,0.25,0.33,0.5,0.8]).apply(lambda s: s.apply(lambda x: format(x, 'g'))))

sizes_counts = Counter(sizes)
print('most common sizes:', sizes_counts.most_common(10))

df_sizes = pd.DataFrame(sorted(sizes))
print(df_sizes)
print('statistics for sizes')
print(df_sizes.describe(percentiles=[0.1,0.2,0.25,0.33,0.5,0.8]).apply(lambda s: s.apply(lambda x: format(x, 'g'))))

sizes_80th_percentile = df_sizes[0].quantile(0.8)
print('80th percentile:', sizes_80th_percentile)

instructions_10k_percentile = stats.percentileofscore(df_instruction_counts[0], 1_000)
print('percentile of 10k instructions:', instructions_10k_percentile)
sizes_10KB_percentile = stats.percentileofscore(df_sizes[0], 10_000)
print('percentile of 10KB:', sizes_10KB_percentile)

# with open('sizes.csv', 'w') as f:
#     for s in sizes:
#         f.write(f'{s}\n')

# df_sizes[0].plot.hist(bins=2**np.arange(4, 28, 0.5))
(df_sizes[0] / 1000).plot.hist(bins=np.arange(0, sizes_80th_percentile / 1000, 5))
# df_sizes[0].plot.hist(bins=np.arange(sizes_80th_percentile, df_sizes[0].max(), 20000))

# plt.xscale("log", basex=2)
# plt.gca().set_xticks(ticks=2**np.arange(4, 27, 2))

plt.ylabel("Number of Binaries")
plt.xlabel("Size (kilobytes)")

plt.tight_layout()

# ft.scale_current_figure(0.9)
plt.savefig('results/size-hist.pdf')

x = df_sizes[0]
y = np.arange(len(df_sizes)) / len(df_sizes) * 100

plt.clf()
plt.step(x, y, where="post")

plt.ylabel("Percent of Binaries")
plt.xlabel("Size (bytes)")
# plt.xlabel("Instruction Count")

plt.xscale("log", basex=2)
plt.gca().set_xticks(ticks=2**np.arange(5, 28, 2))
plt.gca().set_yticks(ticks=np.arange(0, 101, 20))
plt.gca().set_yticks(ticks=np.arange(0, 101, 10), minor=True)

plt.gca().yaxis.set_major_formatter(mpl.ticker.FormatStrFormatter('%d%%'))
plt.grid(True, which="major", axis="y", color=".85", ls="-")
plt.grid(True, which="minor", axis="y", color=".85", ls=":")
plt.grid(True, which="major", axis="x", color=".85", ls="-")
plt.grid(True, which="minor", axis="x", color=".85", ls=":")


plt.tight_layout()
# ft.scale_current_figure(0.9)
plt.savefig("results/size-cdf.pdf")
