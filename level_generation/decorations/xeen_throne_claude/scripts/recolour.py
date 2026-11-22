#!/usr/bin/env python3
"""Recoloured texture sets for the Xeen thrones and the teal statue (lane S, D-66). No Meshy, no Codex.

Throne (MM9 `mm9_deco_throne.glb`, one 1024 atlas: wood and carving left of x 718, red cloth right of it):
  steel  - Ancient steel frame (cool blue-grey, metallic), dark teal cushion   -> DD-17's throne
  gold   - gilded frame, ivory cushion                                         -> DD-08's Euphoria Throne
Statue (MM8 `mm8_deco_elfstatue.glb`, green granite + blade): teal metal (verdigris-free, a cast teal alloy).

Each set: base colour + metallic-roughness (glTF: G roughness, B metallic). Writes work/tex/<set>_{base,mr}.png.
Usage: recolour.py <work dir with throne_img0.png, elf_img1.png, elf_img4.png>"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

work = Path(sys.argv[1])
out = work / 'tex'
out.mkdir(exist_ok=True)
CLOTH_X = 718


def lum(a):
    return (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]) / 255.0


def ramp(t, lo, hi, gamma=1.0):
    t = np.clip(t, 0, 1) ** gamma
    lo, hi = np.array(lo, float), np.array(hi, float)
    return lo + (hi - lo) * t[..., None]


def norm(t, p_lo=2, p_hi=98):
    lo, hi = np.percentile(t, [p_lo, p_hi])
    return (t - lo) / max(hi - lo, 1e-6)


def save(name, rgb):
    Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(out / name)


def mr(shape, metal, rough):
    m = np.zeros(shape[:2] + (3,), float)
    m[..., 1] = rough * 255
    m[..., 2] = metal * 255
    return m


throne = np.array(Image.open(work / 'throne_img0.png').convert('RGB')).astype(float)
L = lum(throne)
frame = np.zeros(L.shape, bool)
frame[:, :CLOTH_X] = True
# Frame and cloth normalised separately so each keeps its full relief.
tf = np.zeros_like(L)
tf[:, :CLOTH_X] = norm(L[:, :CLOTH_X])
tf[:, CLOTH_X:] = norm(L[:, CLOTH_X:])

# Steel: frame in Ancient steel, the cushion dark teal.
base = np.zeros_like(throne)
base[:, :CLOTH_X] = ramp(tf[:, :CLOTH_X], (34, 38, 44), (196, 204, 212), 0.9)
base[:, CLOTH_X:] = ramp(tf[:, CLOTH_X:], (8, 40, 44), (40, 120, 118), 1.0)
save('steel_base.png', base)
m = mr(throne.shape, 0.0, 0.85)
m[:, :CLOTH_X, 2] = 0.85 * 255
m[:, :CLOTH_X, 1] = (0.30 + 0.25 * (1 - tf[:, :CLOTH_X])) * 255
save('steel_mr.png', m)

# Gold: gilded frame, ivory cushion.
base = np.zeros_like(throne)
base[:, :CLOTH_X] = ramp(tf[:, :CLOTH_X], (70, 44, 10), (250, 206, 104), 0.9)
base[:, CLOTH_X:] = ramp(tf[:, CLOTH_X:], (150, 138, 116), (240, 232, 214), 1.0)
save('gold_base.png', base)
m = mr(throne.shape, 0.0, 0.8)
m[:, :CLOTH_X, 2] = 0.9 * 255
m[:, :CLOTH_X, 1] = (0.28 + 0.2 * (1 - tf[:, :CLOTH_X])) * 255
save('gold_mr.png', m)

# Statue: granite and blade to one teal alloy (the blade a little brighter and smoother).
stone = np.array(Image.open(work / 'elf_img1.png').convert('RGB')).astype(float)
t = norm(lum(stone))
# Granite speckle is loud: soften it toward the mean so the figure reads as cast metal, not stone.
t = 0.35 + 0.55 * (t - 0.5) + 0.15
save('teal_stone_base.png', ramp(t, (12, 52, 56), (96, 186, 178), 1.1))
save('teal_stone_mr.png', mr(stone.shape, 0.75, 0.42))
blade = np.array(Image.open(work / 'elf_img4.png').convert('RGB')).astype(float)
tb = norm(lum(blade))
save('teal_blade_base.png', ramp(0.45 + 0.5 * tb, (30, 86, 88), (150, 214, 206), 1.0))
save('teal_blade_mr.png', mr(blade.shape, 0.85, 0.3))
print('wrote', sorted(p.name for p in out.iterdir()))
