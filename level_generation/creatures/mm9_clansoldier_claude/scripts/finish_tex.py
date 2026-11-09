#!/usr/bin/env python3
"""Final names, dark texel block in each image (work/dark_texel.json), head ORM flat. Project folder."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
T = Path('textures'); D = json.load(open('work/dark_texel.json'))
def block(src, dst, k, col=(16, 11, 9)):
    a = np.array(Image.open(src).convert('RGB'))
    S = a.shape[0]; x, y = int(D[k]['u'] * S), int(D[k]['v'] * S); r = max(6, S // 100)
    a[y - r:y + r, x - r:x + r] = col
    Image.fromarray(a).save(dst)
# the sash knot: Meshy's views never saw the two tails (mirrored from one side), so their paint is fur and skin: each tier's sash colour with the paint's own relief
Zf = np.load('work/faces.npz'); Ss = 2048
mk = Image.new('L', (Ss, Ss)); dr = ImageDraw.Draw(mk)
for uv in Zf['uv'][(Zf['mat'] == 1) & (Zf['part'] == 9)]: dr.polygon([(x * Ss, (1 - y) * Ss) for x, y in uv], fill=255)
mk = np.asarray(mk.filter(ImageFilter.GaussianBlur(1.5)), np.float32)[..., None] / 255
SASH = {'a': (0.17, 0.115, 0.07), 'b': (0.30, 0.13, 0.055), 'c': (0.055, 0.13, 0.20)}
for t in 'abc':
    p = T / f'clan_torso_{t}_raw_graded.png'; a_ = np.asarray(Image.open(p).convert('RGB'), np.float32) / 255
    L = a_ @ np.array([.2126, .7152, .0722], np.float32); m_ = L[mk[..., 0] > 0.5].mean()
    rel = np.clip(L / m_, 0.45, 1.7)[..., None]
    Image.fromarray((np.clip(a_ * (1 - mk) + np.array(SASH[t], np.float32) * rel * mk, 0, 1) * 255 + .5).astype('u1')).save(p)
# the cuirass: the grey soft knee that tames the mail also dulls polished plate; MM9's Warrior and Leader chests read bright, so those faces get their light back
cen = Zf['co'].mean(1); chest = (Zf['mat'] == 1) & (Zf['part'] == 1) & (cen[:, 2] > 0.2) & (cen[:, 2] < 0.5) & (np.abs(cen[:, 0]) < 0.25)
mk2 = Image.new('L', (Ss, Ss)); dr = ImageDraw.Draw(mk2)
for uv in Zf['uv'][chest]: dr.polygon([(x * Ss, (1 - y) * Ss) for x, y in uv], fill=255)
mk2 = np.asarray(mk2.filter(ImageFilter.GaussianBlur(2)), np.float32) / 255
for t, gain in (('b', 1.28), ('c', 1.55)):
    p = T / f'clan_torso_{t}_raw_graded.png'; a_ = np.asarray(Image.open(p).convert('RGB'), np.float32) / 255
    sat = a_.max(2) - a_.min(2); g = 1 + (gain - 1) * mk2 * np.clip((0.16 - sat) / 0.08, 0, 1)
    Image.fromarray((np.clip(a_ * g[..., None], 0, 1) * 255 + .5).astype('u1')).save(p)
for t in 'abc':
    block(T / f'clan_torso_{t}_raw_graded.png', T / f'clan_torso_{t}_final.png', 'torso', {'a': (66, 44, 32), 'b': (62, 54, 32), 'c': (36, 46, 60)}[t])      # the skirt's lining: dark cloth that takes light
    block(T / f'clan_head_{t}_raw.png', T / f'clan_head_{t}_final.png', 'head')
# the Leader's thighs: Meshy painted them rust; MM9's trousers are the same dark leather on every tier, so above the knee plate they take the Grunt's texels
Z = np.load('work/faces.npz'); S = Image.open(T / 'clan_limbs_a_raw_graded.png').size[0]
mk = Image.new('L', (S, S)); dr = ImageDraw.Draw(mk)
sel = (Z['mat'] == 0) & (Z['part'] == 5) & (Z['co'][:, :, 2].mean(1) > -0.44)
for uv in Z['uv'][sel]: dr.polygon([(x * S, (1 - y) * S) for x, y in uv], fill=255)
mk = np.asarray(mk.filter(ImageFilter.GaussianBlur(3)), np.float32)[..., None] / 255
a_ = np.asarray(Image.open(T / 'clan_limbs_a_raw_graded.png').convert('RGB'), np.float32); c_ = np.asarray(Image.open(T / 'clan_limbs_c_raw_graded.png').convert('RGB'), np.float32)
Image.fromarray((c_ * (1 - mk) + a_ * mk).astype('u1')).save(T / 'clan_limbs_c_raw_graded.png')
for t in 'ac':
    block(T / f'clan_limbs_{t}_raw_graded.png', T / f'clan_limbs_{t}_final.png', 'limbs')
Image.fromarray(np.dstack([np.full((64, 64), 255, 'u1'), np.full((64, 64), 190, 'u1'), np.zeros((64, 64), 'u1')])).save(T / 'clan_head_orm.png')
print('FINISH done')
