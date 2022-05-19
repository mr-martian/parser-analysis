#!/usr/bin/env python3

from udapi.core.block import Block

from collections import defaultdict

class Pattern:
    ALL_PATTERNS = defaultdict(lambda: defaultdict(list))
    # {level: {name: [obj]}}

    def __init__(self, name, structure, level=1):
        self.name = name
        self.structure = structure
        self.level = level
        Pattern.ALL_PATTERNS[level][name].append(self)

    def sub_match(self, node, pat, prev_refs):
        if 'upos' in pat and pat['upos'] != node.upos:
            return []
        if 'deprel' in pat and pat['deprel'] != node.deprel:
            return []
        refs = prev_refs.copy()
        for key, val_ in pat.items():
            if key in ['upos', 'deprel', 'children']:
                continue
            val = val_
            if isinstance(val, dict) and 'ref' in val:
                if val['ref'] in refs:
                    val = refs[val['refs']]
                else:
                    val = node.feats[key] or node.misc[key]
                    if val:
                        refs[val_['refs']] = val
                    else:
                        return []
            if val != node.feats[key] and val != node.misc[key]:
                return []
        prev = [(refs, [], [])]
        if 'children' in pat:
            pch = pat['children']
            nch = node.children
            if len(nch) < len(pch):
                return []
            for p in pch:
                new_prev = []
                for ref, ch, sibs in prev:
                    for n in nch:
                        if n.ord in sibs:
                            continue
                        for r, c in self.sub_match(n, p, ref):
                            new_prev.append((r, ch+c, sibs+[n.ord]))
                prev = new_prev
        return [(x[0], [node.ord]+x[1]+x[2]) for x in prev]

    def matches(self, node):
        return [x[1] for x in self.sub_match(node, self.structure, {})]

    def find_matching(self, node):
        for n in node.descendants(add_self=True):
            yield from self.matches(n)

class Constructions(Block):
    def __init__(self, level=1, **kwargs):
        self.level = level
        super().__init__(**kwargs)

    def add_pat(self, node, name):
        key = 'Construction'
        val = name
        if node.misc[key]:
            ls = node.misc[key].split(',') + [name]
            val = ','.join(ls)
        node.misc[key] = val

    def process_tree(self, tree):
        for name, pats in Pattern.ALL_PATTERNS[self.level].items():
            match = set()
            for pat in pats:
                for nodes in pat.find_matching(tree):
                    match.update(nodes)
            if match:
                for n in tree.descendants(add_self=True):
                    if n.ord in match:
                        self.add_pat(n, name)

def leaf(upos, deprel):
    return {'upos': upos, 'deprel': deprel}

Pattern('NP-coord',
        {
            'upos': 'NOUN',
            'children': [
                {
                    'upos': 'NOUN',
                    'deprel': 'conj',
                    'children': [leaf('CCONJ', 'cc')]
                }
            ]
        }, level=1)

Pattern('NP-NP-cop',
        {
            'upos': 'NOUN',
            'children': [
                leaf('NOUN', 'nsubj'),
                leaf('AUX', 'cop')
            ]
        }, level=1)
