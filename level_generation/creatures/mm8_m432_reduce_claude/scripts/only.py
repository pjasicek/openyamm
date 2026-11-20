#!/usr/bin/env python3
"""Keep set for a one-region test: every face outside region R (work/regions.npy) kept, plus the soles; prints the
ladder ratios that cut region R to each of the given ratios. Usage: only.py <R> <q,q,..> -> work/keep_only<R>.npy"""
import sys
import numpy as np
reg = np.load('work/regions.npy'); soles = np.load('work/soles.npy'); R = int(sys.argv[1])
keep = (reg != R) | soles; free = (~keep).sum()
np.save(f'work/keep_only{R}.npy', keep)
print(','.join(f'{(keep.sum() + q * free) / len(reg):.4f}' for q in map(float, sys.argv[2].split(','))))
