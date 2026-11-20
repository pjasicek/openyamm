#!/usr/bin/env python3
"""Ladder ratios for a keep/groups config: given REA_GROUP_RATIOS and body (label 0) ratios, print the total ratios.
Usage: REA_GROUP_RATIOS=.. totals.py <name> <body ratio,...>"""
import os, sys
import numpy as np
keep = np.load(f'work/keep_{sys.argv[1]}.npy'); g = np.load(f'work/groups_{sys.argv[1]}.npy')
gr = {int(k): float(x) for k, x in (kv.split(':') for kv in os.environ['REA_GROUP_RATIOS'].split(','))}
fixed = keep.sum() + sum(int(((g == k) & ~keep).sum() * q) for k, q in gr.items())
free = ((g == 0) & ~keep).sum()
print(','.join(f'{(fixed + rb * free) / len(g):.4f}' for rb in map(float, sys.argv[2].split(','))))
