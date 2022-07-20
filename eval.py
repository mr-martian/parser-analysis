#!/usr/bin/env python3

import argparse
from collections import Counter

parser = argparse.ArgumentParser()
parser.add_argument('gold', action='store')
parser.add_argument('system', action='store')
parser.add_argument('-s', '--select', choices=['uas', 'las', 'uas-abs', 'las-abs'], default='table')
args = parser.parse_args()

total = Counter()
correct_uas = Counter()
correct_las = Counter()

def blocks(fin):
    cur = []
    for line in fin:
        if not line.strip():
            if cur:
                yield cur
            cur = []
        elif line.startswith('#'):
            continue
        else:
            cur.append(line.strip())
    if cur:
        yield cur

with open(args.gold) as fgold:
    with open(args.system) as fsys:
        for i, (blg, bls) in enumerate(zip(blocks(fgold), blocks(fsys)), 1):
            if len(blg) != len(bls):
                print(f'Sentences at position {i} have different numbers of words')
                continue
            for gln, sln in zip(blg, bls):
                gls = gln.split('\t')
                sls = sln.split('\t')
                keys = ['']
                for feat in gls[9].split('|'):
                    if feat.startswith('Construction='):
                        keys += feat.split('=')[1].split(',')
                total.update(keys)
                if gls[6] == sls[6]:
                    correct_uas.update(keys)
                    if gls[7] == sls[7]:
                        correct_las.update(keys)

def table():
    rows = [['Construction', 'Words', 'Head Correct', 'UAS', 'Label Correct', 'LAS']]
    for k in sorted(total.keys()):
        rows.append([
            k or '[ALL]',
            str(total[k]),
            str(correct_uas[k]),
            '{:.2%}'.format(correct_uas[k] / total[k]),
            str(correct_las[k]),
            '{:.2%}'.format(correct_las[k] / total[k])
        ])
    widths = [max(len(x[i]) for x in rows) for i in range(6)]
    pat = ' | '.join('{0[%s]:>{1[%s]}}' % (i, i) for i in range(6))
    head = pat.format(rows[0], widths)
    print(head)
    print('-'*len(head))
    for row in rows[1:]:
        print(pat.format(row, widths))

if args.select == 'table':
    table()
else:
    ls = []
    for k in sorted(total.keys()):
        if not k: continue
        t = total[k]
        u = correct_uas[k]
        l = correct_las[k]
        ls.append((u/t, t-u, l/t, t-l, k))
    ks = ['uas', 'uas-abs', 'las', 'las-abs']
    k = ks.index(args.select)
    ls2 = [(x[k], x[4]) for x in ls]
    ls2.sort(reverse=('abs' in args.select))
    for it in ls2[:5]:
        print(it[1])
