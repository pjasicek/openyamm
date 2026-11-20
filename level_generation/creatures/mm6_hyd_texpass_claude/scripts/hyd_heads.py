"""Head index (1-5) of each triangle of the heads set (work/lod0_before_heads.npz): the k whose Head<k> and Neck<k>_*
bones carry the most weight over the triangle's corners. Usage as a module, or: hyd_heads.py (prints counts)."""
import re
import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parents[1]


def head_of_triangle(d=None):
    d = d if d is not None else np.load(PROJECT / 'work' / 'lod0_before_heads.npz')
    names = [str(n) for n in d['joint_names']]
    score = np.zeros((len(d['tri']), 6))
    for k in range(1, 6):
        hit = np.array([bool(re.match(rf'^(Head{k}|Neck{k}_\d+)$', n)) for n in names])
        w = np.where(hit[d['joints']], d['weights'], 0).sum(1)
        score[:, k] = w[d['tri']].mean(1)
    return score.argmax(1), score.max(1)


if __name__ == '__main__':
    k, s = head_of_triangle()
    print({int(i): int((k == i).sum()) for i in range(6)}, 'min score', float(s.min()))
