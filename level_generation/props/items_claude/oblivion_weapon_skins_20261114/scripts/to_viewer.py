#!/usr/bin/env python3
"""The in-game captures as review JPEGs (README.md, "In-game checks"): ingame/<tag>/<template>_<place>/<tier>_<pose>.png
-> <viewer dir>/<template>_<place>_<tier>_<pose>.jpg, 1280 x 720, quality 82 (the skins viewer's naming: tier t0..t4 or
ours, pose idle|swing|swing2). Usage: to_viewer.py <tag> <viewer img dir> [template ...]"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
tag, dest, only = sys.argv[1], sys.argv[2], set(sys.argv[3:])
root = os.path.join(PROJECT, 'ingame', tag)
os.makedirs(dest, exist_ok=True)
count = 0
for folder in sorted(os.listdir(root)):
    template, _, place = folder.rpartition('_')
    if only and template not in only:
        continue
    for file in sorted(os.listdir(os.path.join(root, folder))):
        if not file.endswith('.png'):
            continue
        name = f'{template}_{place}_{file[:-4]}.jpg'
        Image.open(os.path.join(root, folder, file)).convert('RGB').resize((1280, 720), Image.LANCZOS).save(
            os.path.join(dest, name), quality=82)
        count += 1
print('VIEWER', count, 'images ->', dest)
