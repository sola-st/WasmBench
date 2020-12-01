def print_distribution(counter, min_count=0, total=None):
    if total is None:
        total = sum(counter.values())
    for value, count in counter.most_common():
        if count < min_count:
            continue
        percent = count / total
        print(f'{count:8} ({percent:5.1%}) {value}')
    print(f'{total:8} (100%) total')
