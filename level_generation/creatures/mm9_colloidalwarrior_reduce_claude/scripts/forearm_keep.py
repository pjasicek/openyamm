#!/usr/bin/env python3
"""Forearms kept exactly (AttackMelee2 R forearm depth 0.4 -> 1.0 cm in the arm/hand gate when they were in the shared cut):
body faces whose three vertices are dominated by a Forearm bone (incl. its half helper). Usage: forearm_keep.py <base keep> <out>"""
import sys
import numpy as np
d = np.load('work/mesh_in.npz'); f = d['faces']; names = [str(n) for n in d['names']]
dom = np.array([names[i] for i in d['W'].argmax(1)])
k = np.array([' Forearm' in x for x in dom])[f].all(1) & (d['mat'] == 0)
a = np.load(sys.argv[1]); np.save(sys.argv[2], a | k); print('FOREARM', int(k.sum()), 'faces; keep', int(a.sum()), '->', int((a | k).sum()))
