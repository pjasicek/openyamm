#!/usr/bin/env python3
"""Paint one species' 1024² atlas: work/<atlas>/atlas_basecolor.png (RGBA) and atlas_normal.png. Layout in common.py
(blade strips B0/B1, card regions T0/T1, head slots S0-S7, strips R0/R1). Region tags ('flower' / 'foliage') let the
grading gains in work/<atlas>/grade.json (written by sheet.py from the review render versus the sprite) scale each
group. Usage: make_atlas.py <atlas id>"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import seed, work
from paint import (Canvas, bell, blade_strip, bells, frond, jitter, leaf, mix, pad, petal_band, ray_head, rosette,
                   ruffled_petal, scale, stem, tuft, veined_leaf)

AID = sys.argv[1]
rng = np.random.default_rng(seed(AID, 7))
cv = Canvas()
FOLIAGE, FLOWER = 'foliage', 'flower'
tags = {}

GREEN_STEM = ([0.34, 0.56, 0.24], [0.12, 0.26, 0.08])


def blades(body, edge, base, stripe, variant=(0.86, 1.0, 1.06), **kw):
    blade_strip(cv, rng, 'B0', body, edge, base, stripe, **kw)
    blade_strip(cv, rng, 'B1', [c * variant[0] for c in body], edge, base, mix(stripe, body, 0.3), **kw)
    tags.update(B0=FOLIAGE, B1=FOLIAGE)


def tufts(body, base, stripe, regions=('T0', 'T1'), count=46, **kw):
    for r in regions:
        tuft(cv, rng, r, count, body, base, stripe, **kw)
        tags[r] = FOLIAGE


def stems(top=GREEN_STEM[0], base=GREEN_STEM[1]):
    stem(cv, 'R1', top, base)
    tags['R1'] = FOLIAGE


def leaf_slot(region, body, dark, vein, length=0.92, width=0.62, shape='oval', bend=0.0):
    veined_leaf(cv, rng, region, (0.5, 0.99), 0.0, length, width, bend, body, dark, vein, shape=shape)
    tags[region] = FOLIAGE


def leaf_mass(region, count, body, dark, vein, size=(0.12, 0.2), shape='oval', ellipse=(0.5, 0.56, 0.48, 0.46)):
    """Card filled with many broad leaves (leaf mounds of flower06, flower11/12)."""
    cx, cy, rx, ry = ellipse
    for k in range(count):
        x, y = rng.uniform(0.04, 0.96), rng.uniform(0.06, 0.98)
        if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 > 1.0:
            continue
        depth = 0.7 + 0.6 * (1 - y)
        ln = rng.uniform(*size)
        veined_leaf(cv, rng, region, (x, y), rng.uniform(-1.4, 1.4), ln, ln * rng.uniform(0.5, 0.65),
                    rng.normal(0, 0.2), scale(body, depth), dark, scale(vein, depth), shape=shape, veins=3)
    tags[region] = FOLIAGE


if AID == 'flower01':
    blades([0.22, 0.56, 0.26], [0.05, 0.22, 0.08], [0.04, 0.16, 0.05], [0.50, 0.80, 0.46])
    tufts([0.22, 0.54, 0.25], [0.04, 0.15, 0.05], [0.45, 0.75, 0.42], count=44)
    for slot, k in (('S0', 1.0), ('S1', 1.12), ('S2', 0.86)):
        ray_head(cv, rng, slot, 8, scale([0.84, 0.50, 0.86], k), [0.46, 0.12, 0.48], [1.0, 0.92, 0.45],
                 [0.85, 0.65, 0.2], ray_w=0.44, notch=True, disc=0.11, cup=0.4)
        tags[slot] = FLOWER
    stems()
elif AID == 'flower02':
    blades([0.20, 0.40, 0.15], [0.05, 0.13, 0.04], [0.05, 0.12, 0.04], [0.68, 0.70, 0.36])
    tufts([0.20, 0.40, 0.15], [0.04, 0.11, 0.03], [0.62, 0.64, 0.32], count=50)
    for slot, k in (('S0', 1.0), ('S1', 0.94), ('S2', 1.04)):
        ray_head(cv, rng, slot, 6, scale([1.0, 0.86, 0.22], k), [0.72, 0.50, 0.06], [0.34, 0.24, 0.10],
                 [0.14, 0.09, 0.03], ray_w=0.62, disc=0.2, disc_dots=[0.50, 0.36, 0.14], cup=0.6)
        tags[slot] = FLOWER
    stems()
elif AID == 'flower03':
    blades([0.36, 0.60, 0.24], [0.08, 0.20, 0.05], [0.10, 0.24, 0.06], [0.72, 0.86, 0.56], speckle=[0.70, 0.84, 0.52],
           stripes=3)
    tufts([0.34, 0.58, 0.22], [0.08, 0.18, 0.05], [0.68, 0.84, 0.52], count=44)
    rosette(cv, rng, 'S0', [0.90, 0.20, 0.16], [0.62, 0.06, 0.06], [0.38, 0.02, 0.02], frill=0.05)
    petal_band(cv, rng, 'R0', [0.88, 0.20, 0.16], [0.42, 0.05, 0.05], frill=0.05)
    tags.update(S0=FLOWER, R0=FLOWER)
    leaf_slot('S1', [0.34, 0.60, 0.26], [0.10, 0.26, 0.08], [0.60, 0.78, 0.48])
    leaf_slot('S2', [0.28, 0.52, 0.22], [0.08, 0.22, 0.06], [0.52, 0.70, 0.42], shape='lance')
    stems()
elif AID == 'flower04':
    blades([0.26, 0.52, 0.26], [0.06, 0.18, 0.06], [0.06, 0.18, 0.06], [0.58, 0.78, 0.50])
    tufts([0.26, 0.52, 0.26], [0.06, 0.16, 0.06], [0.55, 0.75, 0.48], count=44)
    for slot in ('S0', 'S1'):
        rosette(cv, rng, slot, [0.99, 0.94, 0.66], [0.88, 0.80, 0.46], [0.72, 0.60, 0.30], frill=0.06,
                edge=[0.90, 0.62, 0.50])
        tags[slot] = FLOWER
    petal_band(cv, rng, 'R0', [0.98, 0.92, 0.64], [0.62, 0.34, 0.30], frill=0.06, tint_bottom=[0.55, 0.20, 0.32])
    tags['R0'] = FLOWER
    leaf_slot('S2', [0.26, 0.50, 0.26], [0.07, 0.20, 0.07], [0.34, 0.56, 0.32], width=0.72)
    leaf_slot('S3', [0.22, 0.44, 0.22], [0.06, 0.18, 0.06], [0.30, 0.50, 0.28], width=0.66)
    stems()
elif AID == 'flower05':
    for region in ('T0', 'T1'):
        for k in range(26):
            side = rng.uniform(-1, 1)
            frond(cv, rng, region, (0.5 + rng.normal(0, 0.08), 1.0), side * 0.8 + rng.normal(0, 0.1),
                  rng.uniform(0.55, 0.95), jitter(rng, [0.20, 0.52, 0.20], 0.1), [0.04, 0.16, 0.05],
                  leaflets=12, leaflet=0.07, bend=side * 0.5)
        tags[region] = FOLIAGE
    for slot in ('S0', 'S1'):
        rosette(cv, rng, slot, [0.92, 0.92, 0.94], [0.80, 0.80, 0.84], [0.86, 0.80, 0.46], frill=0.16,
                per_ring=(11, 10, 9, 7))
        tags[slot] = FLOWER
    petal_band(cv, rng, 'R0', [0.92, 0.92, 0.94], [0.60, 0.60, 0.62], frill=0.16, count=9)
    tags['R0'] = FLOWER
    leaf_slot('S2', [0.66, 0.68, 0.38], [0.34, 0.36, 0.14], [0.70, 0.71, 0.44], width=0.78)
    leaf_slot('S3', [0.58, 0.62, 0.32], [0.28, 0.32, 0.12], [0.63, 0.66, 0.38], width=0.70)
    stems([0.30, 0.55, 0.22], [0.10, 0.24, 0.06])
elif AID == 'flower06':
    blades([0.24, 0.46, 0.18], [0.05, 0.15, 0.04], [0.06, 0.16, 0.04], [0.56, 0.72, 0.42])
    tuft(cv, rng, 'T0', 40, [0.24, 0.46, 0.18], [0.05, 0.14, 0.04], [0.5, 0.68, 0.38])
    tags['T0'] = FOLIAGE
    leaf_mass('T1', 160, [0.26, 0.46, 0.18], [0.06, 0.16, 0.04], [0.48, 0.64, 0.36], size=(0.14, 0.24),
              shape='lance')
    for slot, k in (('S0', 1.0), ('S1', 0.92)):
        ray_head(cv, rng, slot, 22, scale([1.0, 0.84, 0.22], k), [0.82, 0.56, 0.06], [0.56, 0.48, 0.14],
                 [0.32, 0.24, 0.05], ray_w=0.13, disc=0.17, layers=2, cup=0.3)
        tags[slot] = FLOWER
    leaf_slot('S2', [0.28, 0.48, 0.20], [0.07, 0.16, 0.05], [0.50, 0.66, 0.38], shape='lance', width=0.5)
    stems()
elif AID == 'flower07':
    blades([0.26, 0.58, 0.28], [0.06, 0.20, 0.08], [0.05, 0.18, 0.06], [0.55, 0.82, 0.55])
    tuft(cv, rng, 'S2', 30, [0.26, 0.56, 0.28], [0.05, 0.16, 0.06], [0.5, 0.78, 0.5], droop=0.8)
    tags['S2'] = FOLIAGE
    # Bells are painted near white and tinted per spike through COLOR_0 (white, coral, pink, lilac).
    bells(cv, rng, 'T0', [0.97, 0.95, 0.97], [0.66, 0.50, 0.58], [0.40, 0.18, 0.30])
    bells(cv, rng, 'T1', [0.97, 0.95, 0.97], [0.66, 0.50, 0.58], [0.40, 0.18, 0.30], card=True)
    for slot in ('S0', 'S1'):                  # single bells for the near level's bell cards
        bell(cv, rng, slot, 0.5, 0.04, 0.82, 0.92, [0.97, 0.95, 0.97], [0.66, 0.50, 0.58], [0.40, 0.18, 0.30],
             lean=0.08 if slot == 'S1' else 0.0)
    for k in range(7):                         # bud cluster for the spike tip
        cv.ellipse('S3', (0.5 + rng.normal(0, 0.05), 0.12 + k * 0.12), 0.08 + 0.025 * k, 0.07,
                   [0.46, 0.66, 0.32], [0.18, 0.32, 0.12], n=12, cup=0.4)
    cv.stamp('S3', [(0.48, 0.05), (0.52, 0.05), (0.53, 1.0), (0.47, 1.0)], [0.42, 0.62, 0.30], [0.16, 0.30, 0.12])
    tags.update(T0=FLOWER, T1=FLOWER, S0=FLOWER, S1=FLOWER, S3=FOLIAGE)
    stems()
elif AID == 'flower08':
    blades([0.30, 0.68, 0.24], [0.06, 0.24, 0.05], [0.05, 0.20, 0.04], [0.62, 0.88, 0.48])
    tufts([0.30, 0.66, 0.24], [0.05, 0.18, 0.04], [0.58, 0.85, 0.46], count=40, spread=0.7, droop=0.25)
    ruffled_petal(cv, rng, 'S0', [0.90, 0.42, 0.72], [0.50, 0.10, 0.36], [0.99, 0.86, 0.94], frill=0.10)
    ruffled_petal(cv, rng, 'S1', [0.68, 0.18, 0.50], [0.36, 0.04, 0.24], [0.98, 0.80, 0.92], frill=0.12, width=0.92)
    ruffled_petal(cv, rng, 'S3', [0.82, 0.30, 0.62], [0.42, 0.06, 0.30], [0.96, 0.76, 0.90], frill=0.14, width=0.8)
    leaf(cv, 'S2', (0.5, 0.99), 0.0, 0.95, 0.5, 0.0, [0.55, 0.20, 0.50], [0.20, 0.42, 0.16], ridge=0.6, shape='lance')
    tags.update(S0=FLOWER, S1=FLOWER, S2=FLOWER, S3=FLOWER)
    stems([0.36, 0.62, 0.26], [0.12, 0.30, 0.08])
elif AID == 'flower09':
    blades([0.26, 0.50, 0.22], [0.05, 0.16, 0.04], [0.05, 0.14, 0.04], [0.55, 0.74, 0.46])
    tufts([0.26, 0.50, 0.22], [0.05, 0.14, 0.04], [0.5, 0.7, 0.42], count=50, length=(0.45, 0.85))
    for slot, k in (('S0', 1.0), ('S1', 0.95)):
        ray_head(cv, rng, slot, 8, scale([0.98, 0.97, 0.93], k), [0.72, 0.66, 0.58], [1.0, 0.86, 0.16],
                 [0.86, 0.58, 0.04], ray_w=0.30, pointed=True, disc=0.30, disc_dots=[1.0, 0.94, 0.42],
                 edge=[0.46, 0.32, 0.20], cup=0.2)
        tags[slot] = FLOWER
    stems()
elif AID == 'flower10':
    for region in ('T0', 'T1'):
        for k in range(260):                 # dense moss: small rounded leaflets filling a mound, then fern fronds
            x, y = rng.uniform(0.04, 0.96), rng.uniform(0.1, 0.98)
            if ((x - 0.5) / 0.48) ** 2 + ((y - 0.58) / 0.46) ** 2 > 1.0:
                continue
            depth = 0.7 + 0.6 * (1 - y)
            leaf(cv, region, (x, y), rng.uniform(-1.5, 1.5), rng.uniform(0.06, 0.1), rng.uniform(0.04, 0.06),
                 rng.normal(0, 0.3), jitter(rng, scale([0.30, 0.56, 0.16], depth), 0.12), [0.05, 0.16, 0.03],
                 steps=6, shape='oval', ridge=0.5)
        for k in range(60):
            x, y = rng.uniform(0.1, 0.9), rng.uniform(0.25, 1.0)
            frond(cv, rng, region, (x, y), rng.uniform(-1.3, 1.3), rng.uniform(0.18, 0.32),
                  jitter(rng, [0.42, 0.66, 0.22], 0.12), [0.08, 0.22, 0.04], leaflets=10, leaflet=0.05,
                  bend=rng.normal(0, 0.3))
        tags[region] = FOLIAGE
    for slot, k in (('S0', 1.0), ('S1', 0.93), ('S2', 1.0)):
        ray_head(cv, rng, slot, 24, scale([0.98, 0.98, 0.96], k), [0.66, 0.66, 0.68], [0.96, 0.78, 0.18],
                 [0.72, 0.52, 0.06], ray_w=0.13, disc=0.26, disc_dots=[0.98, 0.86, 0.36], cup=0.25)
        tags[slot] = FLOWER
    blades([0.28, 0.54, 0.20], [0.06, 0.18, 0.04], [0.06, 0.16, 0.04], [0.55, 0.75, 0.44])
    stems()
elif AID == 'flower12':
    for region in ('T0', 'T1'):
        leaf_mass(region, 110, [0.20, 0.50, 0.24], [0.03, 0.15, 0.04], [0.42, 0.70, 0.44], size=(0.2, 0.3),
                  shape='oval', ellipse=(0.5, 0.55, 0.48, 0.45))
        for k in range(8):                     # a few painted primulas for distance
            x, y = rng.uniform(0.2, 0.8), rng.uniform(0.25, 0.85)
            for j in range(5):
                a = j / 5 * 2 * math.pi
                cv.ellipse(region, (x + math.cos(a) * 0.022, y + math.sin(a) * 0.022), 0.02, 0.02,
                           [0.95, 0.42, 0.55], [0.72, 0.20, 0.32], n=10)
            cv.ellipse(region, (x, y), 0.01, 0.01, [1.0, 0.9, 0.3], [0.8, 0.6, 0.1], n=8)
    for slot, k in (('S0', 1.0), ('S1', 0.88)):
        ray_head(cv, rng, slot, 5, scale([0.95, 0.42, 0.56], k), [0.66, 0.16, 0.28], [1.0, 0.90, 0.24],
                 [0.86, 0.62, 0.10], ray_w=0.6, notch=True, disc=0.2, cup=0.35)
        tags[slot] = FLOWER
    leaf_slot('S2', [0.22, 0.52, 0.26], [0.04, 0.16, 0.05], [0.44, 0.72, 0.46], shape='lance', width=0.55)
    blades([0.24, 0.58, 0.26], [0.05, 0.20, 0.07], [0.04, 0.16, 0.05], [0.50, 0.80, 0.48])
    tuft(cv, rng, 'S3', 26, [0.24, 0.56, 0.26], [0.04, 0.15, 0.05], [0.5, 0.78, 0.48])
    tags['S3'] = FOLIAGE
    stems()
elif AID == 'flower16':
    ray_head(cv, rng, 'S0', 11, [0.97, 0.97, 1.0], [0.62, 0.62, 0.82], [0.9, 0.9, 0.9], [0.9, 0.9, 0.9],
             ray_w=0.3, pointed=True, disc=0.0, cup=0.3)
    ray_head(cv, rng, 'S1', 9, [0.98, 0.98, 1.0], [0.70, 0.70, 0.86], [1.0, 0.86, 0.24], [0.86, 0.62, 0.08],
             ray_w=0.34, pointed=True, disc=0.30, disc_dots=[1.0, 0.95, 0.5], cup=0.3)
    tags.update(S0=FLOWER, S1=FLOWER)
    for slot, k in (('S2', 1.0), ('S3', 0.85)):
        pad(cv, rng, slot, scale([0.26, 0.58, 0.28], k), [0.08, 0.26, 0.10], [0.44, 0.72, 0.42])
        tags[slot] = FOLIAGE
    # bud side (lathe): pale pink-white petals over green sepals
    petal_band(cv, rng, 'R0', [0.96, 0.86, 0.90], [0.40, 0.56, 0.30], rows=1, count=5)
    tags['R0'] = FLOWER
    blades([0.22, 0.58, 0.26], [0.05, 0.20, 0.07], [0.04, 0.16, 0.05], [0.48, 0.80, 0.46])
    tuft(cv, rng, 'T1', 46, [0.22, 0.56, 0.26], [0.04, 0.15, 0.05], [0.46, 0.76, 0.44], spread=0.9, droop=0.3)
    tags['T1'] = FOLIAGE
    for k in range(16):                        # pad cluster card for the far level
        x, y = rng.uniform(0.15, 0.85), rng.uniform(0.45, 0.85)
        r = rng.uniform(0.09, 0.14)
        cv.ellipse('T0', (x, y), r, r * 0.45, [0.30, 0.62, 0.30], [0.10, 0.30, 0.12], n=20, cup=0.3)
    for k in range(5):
        x, y = rng.uniform(0.25, 0.75), rng.uniform(0.4, 0.7)
        cv.ellipse('T0', (x, y), 0.06, 0.035, [0.98, 0.98, 1.0], [0.72, 0.72, 0.88], n=14)
        cv.ellipse('T0', (x, y + 0.005), 0.018, 0.012, [1.0, 0.86, 0.24], [0.86, 0.62, 0.08], n=10)
    tags['T0'] = FOLIAGE
    stems()
else:
    raise SystemExit('unknown atlas ' + AID)

out = work(AID)
grade_path = os.path.join(out, 'grade.json')
if os.path.exists(grade_path):
    gains = json.load(open(grade_path))
    for region, group in tags.items():
        if group in gains:
            cv.grade(region, gains[group])
    print('GRADED', AID, gains)
cv.save(os.path.join(out, 'atlas_basecolor.png'), os.path.join(out, 'atlas_normal.png'))
json.dump(tags, open(os.path.join(out, 'tags.json'), 'w'), indent=1)
print('ATLAS', AID, sorted(tags.items()))
