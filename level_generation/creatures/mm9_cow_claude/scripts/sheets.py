#!/usr/bin/env python3
"""Review sheets from viewer shots: sheets.py <cow|goat> compare|angles|texture"""
import sys, subprocess, json
from pathlib import Path
from PIL import Image, ImageDraw
n, kind = sys.argv[1], sys.argv[2]
ROOT = Path('/home/pjasicek/github/OpenYAMM'); P = ROOT / f'level_generation/creatures/mm9_{n}_claude'
SH = ROOT / 'level_generation/creatures/mm9_cow_claude/scripts/shots.sh'
BL = ROOT / 'level_generation/creatures/mm9_cow_claude/scripts/bl.sh'
tiers = {'cow': ['cow_a', 'cow_b'], 'goat': ['goat']}[n]
pairs = {'cow': [('Stand', 'Standing', 0.0), ('Walk', 'Walking', 0.3), ('Run', 'Running', 0.1), ('Fidget1', 'Fidget', 1.1), ('Wince1', 'Hit', 0.5), ('Die1', 'Death', 1.2), ('Die1', 'Dead', 2.39)],
         'goat': [('Stand', 'Standing', 0.0), ('Walk', 'Walking', 0.3), ('Run', 'Running', 0.1), ('Fidget1', 'Fidget', 1.1), ('HAttack1', 'AttackMelee', 0.3), ('Wince1', 'Hit', 0.4), ('Die1', 'Death', 1.0), ('Die1', 'Dead', 1.89)]}[n]
ortho, cen = {'cow': (3.6, '0,0,0.8'), 'goat': (2.2, '0,0.05,0.5')}[n]


def shots(tier, outdir, specs):
    subprocess.run([str(SH), n, tier, outdir] + specs, check=True)


def grid(files, cols, cell, out, labels=None):
    rows = (len(files) + cols - 1) // cols
    s = Image.new('RGB', (cell[0] * cols, cell[1] * rows), (40, 40, 44))
    d = ImageDraw.Draw(s)
    for k, f in enumerate(files):
        im = Image.open(f).convert('RGBA')
        bg = Image.new('RGBA', im.size, (90, 92, 98, 255)); bg.alpha_composite(im)
        s.paste(bg.convert('RGB').resize(cell), (cell[0] * (k % cols), cell[1] * (k // cols)))
        if labels:
            d.text((cell[0] * (k % cols) + 6, cell[1] * (k // cols) + 4), labels[k], fill=(255, 255, 160))
    s.save(out)
    print('SHEET', out)


if kind == 'compare':
    specs, files, labels = [], [], []
    for i, (src, role, t) in enumerate(pairs):
        specs.append(f'c{i}:{role}:{t}:right:body')
    shots(tiers[0], 'sheet_shots', specs)
    rig = P / f'work/mm9_{n}_rig.blend'
    for src in sorted({p[0] for p in pairs}):
        secs = ','.join(str(p[2] if p[1] != 'Dead' else p[2]) for p in pairs if p[0] == src)
        subprocess.run([str(BL), n, 'mm9_frames.py', str(rig), str(P / 'review/sheet_shots/mm9'), src, secs, 'right', '700', str(ortho), cen], check=True, stdout=subprocess.DEVNULL)
    for i, (src, role, t) in enumerate(pairs):
        files.append(P / f'review/sheet_shots/mm9/{src}_{t}_right.png'); labels.append(f'MM9 {src} {t}s')
    for i, (src, role, t) in enumerate(pairs):
        files.append(P / f'review/sheet_shots/c{i}.png'); labels.append(f'ours (viewer) {role} {t}s')
    grid(files, len(pairs), (360, 300), P / 'review/sheet_mm9_vs_ours.png', labels)
elif kind == 'angles':
    views = [('right', 'body'), ('front', 'body'), ('quarter', 'body'), ('rear', 'body')]
    cam = {'cow': '-1.8,-0.2,1.5:0,0.55,0.1', 'goat': '-1.0,-0.1,0.9:0,0.33,0.1'}[n]
    for tier in tiers:
        specs, files, labels = [], [], []
        for clip, t in {'cow': [('Standing', 0.0), ('Walking', 0.6), ('Fidget', 1.1)], 'goat': [('Standing', 0.0), ('Walking', 0.5), ('AttackMelee', 0.3)]}[n]:
            for v, f in views:
                nm = f'a_{tier}_{clip}_{v}'
                specs.append(f'{nm}:{clip}:{t}:{v}:{f}'); files.append(P / f'review/sheet_shots/{nm}.png'); labels.append(f'{tier} {clip} {t}s {v}')
            nm = f'a_{tier}_{clip}_below'
            specs.append(f'{nm}:{clip}:{t}:quarter:body:{cam}'); files.append(P / f'review/sheet_shots/{nm}.png'); labels.append(f'{tier} {clip} {t}s below')
        shots(tier, 'sheet_shots', specs)
        grid(files, 5, (400, 295), P / f'review/sheet_angles_{tier}.png', labels)
elif kind == 'texture':
    cams = {'cow': [('head', 'Standing:0.0:quarter:head:-0.9,1.5,2.15:0,1.32,1.05'), ('face', 'Standing:0.0:front:head:0,1.3,2.5:0,1.3,1.1'), ('mouth', 'Fidget:1.1:quarter:head'), ('coat', 'Standing:0.0:right:body:-1.3,1.1,0.2:0,0.9,0.1'), ('udder', 'Standing:0.0:rear:arms'), ('hoof', 'Standing:0.0:quarter:feet:-0.7,0.25,0.9:-0.2,0.12,0.4')],
            'goat': [('head', 'Standing:0.0:quarter:head:-0.5,0.95,1.15:0,0.82,0.55'), ('face', 'Standing:0.5:front:head'), ('mouth', 'AttackMelee:0.3:right:head'), ('coat', 'Standing:0.0:right:body:-0.8,0.7,0.1:0,0.55,0.1'), ('rear', 'Standing:0.0:rear:arms'), ('hoof', 'Standing:0.0:quarter:feet:-0.45,0.15,0.55:-0.1,0.08,0.25')]}[n]
    for tier in tiers:
        specs, files, labels = [], [], []
        for nm, sp in cams:
            specs.append(f't_{tier}_{nm}:{sp}'); files.append(P / f'review/sheet_shots/t_{tier}_{nm}.png'); labels.append(f'{tier} {nm}')
        shots(tier, 'sheet_shots', specs)
        grid(files, 3, (640, 470), P / f'review/sheet_texture_{tier}.png', labels)
