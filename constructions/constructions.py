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

    def compare(self, node, pat):
        if isinstance(pat, str):
            if ':' in node or ':' in pat:
                return node == pat or node.startswith(pat+':')
            return node == pat
        elif isinstance(pat, list):
            return any(self.compare(node, p) for p in pat)
        else:
            return False

    def sub_match(self, node, pat, prev_refs):
        if not self.compare(node.upos, pat.get('upos', node.upos)):
            return []
        if not self.compare(node.deprel, pat.get('deprel', node.deprel)):
            return []
        if 'side' in pat:
            if pat['side'] == 'left' and node.ord > node.parent.ord:
                return []
            if pat['side'] == 'right' and node.ord < node.parent.ord:
                return []
        refs = prev_refs.copy()
        for key, val_ in pat.items():
            if key in ['upos', 'deprel', 'children', 'not', 'side']:
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
        if 'not' in pat:
            new_prev = []
            for ref, ch, sibs in prev:
                for sub_pat in pat['not']:
                    m = self.sub_match(node, sub_pat, ref)
                    if m: break
                else:
                    new_prev.append((ref, ch, sibs))
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

NOUNish = ['NOUN', 'PRON', 'PROPN']
NOUNsubj = leaf(NOUNish, 'nsubj')

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

Pattern('PP-coord',
        {
            'upos': NOUNish,
            'children': [
                leaf('ADP', 'case'),
                {
                    'upos': NOUNish,
                    'deprel': 'conj',
                    'children': [leaf('ADP', 'case')]
                },
                leaf('CCONJ', 'cc')
            ]
        }, level=1)

Pattern('NP-NP-cop',
        {
            'upos': NOUNish,
            'children': [
                NOUNsubj,
                leaf('AUX', 'cop')
            ]
        }, level=1)

Pattern('NP-cop-no-subj',
        {
            'upos': NOUNish,
            'children': [
                leaf('AUX', 'cop')
            ],
            'not': [
                {'children': [NOUNsubj]}
            ]
        }, level=1)

Pattern('NP-NP-no-cop',
        {
            'upos': NOUNish,
            'children': [NOUNsubj],
            'not': [{'children': [leaf('AUX', 'cop')]}]
        }, level=1)

Pattern('VP-coord',
        {
            'upos': 'VERB',
            'children': [
                {
                    'upos': ['VERB', 'AUX'],
                    'deprel': 'conj',
                    'children': [leaf('CCONJ', 'cc')]
                }
            ]
        }, level=1)

Pattern('VP-coord',
        {
            'upos': 'AUX',
            'children': [
                {
                    # don't include AUX here, since that might be
                    # AUX-AUX coordination instead
                    'upos': 'VERB',
                    'deprel': 'conj',
                    'children': [leaf('CCONJ', 'cc')]
                }
            ]
        }, level=1)

Pattern('VP-coord',
        {
            'upos': 'AUX',
            'deprel': ['root', 'parataxis', 'conj', 'ccomp'],
            'children': [
                {
                    'upos': 'AUX',
                    'deprel': 'conj',
                    'children': [leaf('CCONJ', 'cc')]
                }
            ]
        }, level=1)

Pattern('NP-PP',
        {
            'upos': NOUNish,
            'children': [
                {
                    'upos': NOUNish,
                    'deprel': 'nmod',
                    'children': [leaf('ADP', 'case')]
                }
            ]
        }, level=1)

Pattern('VP-PP',
        {
            'upos': 'VERB',
            'children': [
                {
                    'upos': NOUNish,
                    'deprel': 'obl',
                    'children': [leaf('ADP', 'case')]
                }
            ]
        }, level=1)

Pattern('Transitive-Verb',
        {
            'upos': 'VERB',
            'children': [
                {'deprel': 'nsubj'},
                {'deprel': 'obj'}
            ]
        }, level=1)

Pattern('Transitive-no-subj',
        {
            'upos': 'VERB',
            'children': [{'deprel': 'obj'}],
            'not': [{'children': [NOUNsubj]}]
        }, level=1)

Pattern('Multi-Conj',
        {
            'children': [
                {'deprel': 'conj'},
                {'deprel': 'conj'}
            ]
        }, level=1)

Pattern('Obl-to-non-verb',
        {
            'upos': ['ADJ', 'ADV', 'NOUN'],
            'children': [
                {'deprel': 'nsubj'},
                {
                    'deprel': 'obl',
                    'children': [
                        {'deprel': 'case'}
                    ]
                }
            ]
        }, level=1)

Pattern('Elided-Coord-Verb',
        {
            'upos': 'VERB',
            'children': [
                {
                    'deprel': 'conj',
                    'not': [{'upos': ['VERB', 'AUX']}],
                    'children': [{'deprel': 'orphan'}]
                }
            ]
        }, level=1)

# TODO: doesn't account for NUM as head of NP coordinated with other NP
Pattern('Complex-Numeral',
        {
            'upos': 'NUM',
            'children': [
                {
                    'upos': 'NUM',
                    'deprel': ['flat', 'conj', 'compound']
                }
            ]
        }, level=1)

Pattern('Verbal-Negation',
        {
            'upos': 'VERB',
            'children': [
                {
                    'deprel': 'advmod',
                    'Polarity': 'Neg'
                }
            ]
        }, level=1)

Pattern('Making',
        {
            'upos': 'VERB',
            'children': [
                leaf('NOUN', 'obj'),
                leaf('NOUN', 'xcomp')
            ]
        }, level=1)

Pattern('Title',
        {
            'upos': 'PROPN',
            'children': [leaf('NOUN', 'appos')]
        }, level=1)

Pattern('Title',
        {
            'upos': 'NOUN',
            'children': [leaf('PROPN', 'flat')]
        }, level=1)

Pattern('Quantified-noun',
        {
            'upos': 'NOUN',
            'children': [leaf('NUM', 'nummod')]
        }, level=1)

Pattern('Quantified-noun',
        {
            'upos': 'NOUN',
            'children': [
                {'upos': ['ADJ', 'NUM'], 'deprel': 'amod', 'NumType': 'Ord'}
            ],
        }, level=1)

Pattern('Nominal-acl',
        {
            'upos': 'NOUN',
            'children': [
                {
                    'deprel': 'acl',
                    'not': [
                        {'upos': 'VERB'},
                        {'children': [{'deprel': 'nsubj'}]}
                    ]
                }
            ]
        }, level=1)

Pattern('PP-acl',
        {
            'upos': 'NOUN',
            'deprel': 'acl',
            'children': [leaf('ADP', 'case')]
        }, level=1)

Pattern('Maybe-resumptive-subject',
        {
            'upos': 'VERB',
            'children': [
                {'deprel': 'nsubj'},
                {'deprel': 'dislocated', 'side': 'left'}
            ]
        }, level=1) #TODO: maybe level2

Pattern('Controlled-subj',
        {
            'children': [
                NOUNsubj,
                {
                    'deprel': 'xcomp',
                    'not': [{'children': [NOUNsubj]}]
                }
            ]
        }, level=1)

Pattern('Raised-subj',
        {
            'children': [
                leaf(NOUNish, 'obj'),
                {'deprel': 'xcomp', 'not': [{'children': [NOUNsubj]}]}
            ]
        }, level=1)

Pattern('Predicate-adj',
        {
            'upos': 'ADJ',
            'children': [
                NOUNsubj,
                leaf('AUX', 'cop')
            ]
        }, level=1)

Pattern('NUM-of-the-NOUN',
        {
            'upos': 'NUM',
            'children': [
                {
                    'upos': 'NOUN',
                    'deprel': 'nmod',
                    'children': [leaf('ADP', 'case'), leaf('DET', 'det')]
                }
            ]
        }, level=1)

Pattern('NUM-of-the-NOUN',
        {
            'upos': 'NUM',
            'children': [
                {
                    'upos': 'NOUN',
                    'deprel': 'nmod',
                    'children': [leaf('DET', 'det')]
                }
            ]
        }, level=1)

Pattern('NUM-of-the-NOUN',
        {
            'upos': 'NUM',
            'children': [
                {
                    'upos': NOUNish,
                    'deprel': 'nmod',
                    'children': [leaf('ADP', 'case')]
                }
            ]
        }, level=1)

Pattern('NUM-of-the-NOUN',
        {
            'upos': 'NUM',
            'children': [leaf('NOUN', 'nmod')]
        }, level=1)

clause_dep = ['xcomp', 'ccomp', 'advcl', 'acl', 'csubj']

Pattern('Clause-bracketing',
        {
            'children': [
                {
                    'deprel': clause_dep,
                    'children': [{'deprel': clause_dep}]
                }
            ]
        }, level=1)

Pattern('Clause-bracketing',
        {
            'children': [
                {'deprel': clause_dep},
                {'deprel': clause_dep}
            ]
        }, level=1)

Pattern('Poss-PRON',
        {
            'upos': 'NOUN',
            'children': [leaf('PRON', 'nmod:poss')]
        }, level=1)

Pattern('NP-bracketing',
        {
            'upos': NOUNish,
            'children': [
                leaf(NOUNish, 'nmod'),
                leaf(NOUNish, 'nmod')
            ]
        }, level=1)

Pattern('NP-bracketing',
        {
            'upos': NOUNish,
            'children': [
                {
                    'upos': NOUNish,
                    'deprel': 'nmod',
                    'children': [leaf(NOUNish, 'nmod')]
                }
            ]
        }, level=1)

Pattern('Complex-AdjP',
        {
            'upos': 'ADJ',
            'deprel': ['amod', 'advmod'],
            'children': [{'deprel': ['obl', 'nmod']}]
        }, level=1)

Pattern('Shared-ADP',
        {
            'upos': NOUNish,
            'children': [
                leaf('ADP', 'case'),
                {
                    'upos': NOUNish,
                    'deprel': 'conj',
                    'not': [{'children': [leaf('ADP', 'case')]}]
                }
            ]
        }, level=1)

Pattern('Shared-subj',
        {
            'upos': 'VERB',
            'children': [
                leaf(NOUNish, 'nsubj'),
                {
                    'upos': 'VERB',
                    'deprel': 'conj',
                    'not': [{'children': [leaf(NOUNish, 'nsubj')]}]
                }
            ]
        }, level=1)

Pattern('Subordinated-clause',
        {
            'upos': 'VERB',
            'children': [
                {
                    'upos': 'VERB',
                    'deprel': ['advcl', 'ccomp'],
                    'children': [leaf('SCONJ', 'mark')]
                }
            ]
        }, level=1)

Pattern('Long-name',
        {
            'upos': 'PROPN',
            'children': [leaf('PROPN', 'flat'), leaf('PROPN', 'flat')]
        }, level=1)

Pattern('Name-list',
        {
            'upos': 'PROPN',
            'children': [
                leaf('PROPN', 'flat'),
                {
                    'upos': 'PROPN',
                    'deprel': ['conj', 'parataxis'],
                    'children': [leaf('PROPN', 'flat')]
                }
            ]
        }, level=1)
