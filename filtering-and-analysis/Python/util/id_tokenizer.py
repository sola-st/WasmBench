import re


non_alpha_regex = re.compile(r'[^a-zA-Z]')
alpha_regex = re.compile(r'[a-zA-Z]+')


def split_camel_case(id):
    return re.findall(r'^[a-z]+|[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))', id)


def split_non_alpha(id):
    return re.split(non_alpha_regex, id)


def filter_tokens(tokens):
    return [t for t in tokens if alpha_regex.match(t)]


def tokenize(id):
    subtokens = []
    raw_subtokens = split_non_alpha(id)
    for s in raw_subtokens:
        subtokens.extend(split_camel_case(s))

    # remove non-alpha tokens
    filtered = filter_tokens(subtokens)

    return filtered
