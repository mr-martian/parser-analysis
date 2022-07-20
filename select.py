#!/usr/bin/env python3

import sys, argparse

parser = argparse.ArgumentParser('Select sentences from a treebank containing particular constructions')
parser.add_argument('in_treebank', action='store')
parser.add_argument('out_treebank', action='store')
parser.add_argument('-c', '--count', type=int, default=100)
args = parser.parse_args()

def read_blocks(fin):
    cur = []
    while True:
        l = fin.read()
        if not l.strip():
            if cur:
                yield '\n'.join(cur)
                cur = []
            if not l:
                break
        else:
            cur.append(l.strip())

def get_constructions(block):
    ret = set()
    for l in block.splitlines():
        ls = l.split('\t')
        if len(ls) != 10: continue
        for m in ls[9].split('|'):
            if m.startswith('Construction='):
                ret.update(m.split('=')[1].split(','))
    return ret

cons = set()
for l in sys.stdin().readlines():
    cons.add(l.strip())

count = 0
with open(args.in_treebank) as fin:
    with open(args.out_treebank, 'w') as fout:
        for block in read_blocks(fin):
            # TODO: balanced selection of constructions?
            if len(cons) == 0 or not cons.isdisjoint(get_constructions(block)):
                fout.write(block + '\n\n')
                count += 1
                if count == args.count:
                    break
