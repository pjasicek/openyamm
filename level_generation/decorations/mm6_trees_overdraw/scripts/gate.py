#!/usr/bin/env python3
"""Step 4: gates and the before/after sheet for one tree (system Python; runs render.py in Blender).

Installed (work/<id>/installed.glb) against new (work/<id>/mm6_deco_<id>.glb), same renderer and framing:
  - coverage (opaque pixels) and mean colour (sRGB /255 over opaque pixels) per LOD 0..2, mean over the eye,
    three-quarter and side views: |coverage change| <= 3 %, max channel colour change <= 3;
  - neighbouring LOD steps (eye view, LOD0-1-2-impostor): colour <= max(4, installed step + 1) /255, coverage <= max(5 %, installed step);
  - card layers (overdraw.py: no depth test, and in front of the opaque depth), mean over the three views;
  - triangles per LOD no higher than installed;
  - black patches: from next to the trunk looking up 60 degrees and a low three-quarter view, the share of opaque
    pixels darker than luminance 12 at most the installed model's + 0.5 %.
Writes work/<id>/gate.json and review/<id>/before_after.png. Usage: gate.py <id>"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, glb, overdraw

tid = sys.argv[1]
spec = common.load(tid); W = spec['work']; R = spec['review']
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(W, 'r'), exist_ok=True); os.makedirs(os.path.join(W, 'heat'), exist_ok=True)
MODELS = {'inst': os.path.join(W, 'installed.glb'), 'new': os.path.join(W, spec['glb'])}
VIEWS = ['eye', 'three_quarter', 'side']
DETAIL = ['close', 'under', 'trunk', 'up', 'low3q']


def render(tag):
    prefix = os.path.join(W, 'r', tag)
    stamp = prefix + '.stamp'
    src = MODELS[tag]
    if os.path.exists(stamp) and open(stamp).read() == str(os.path.getmtime(src)):
        return prefix
    subprocess.run([common.BLENDER, '--background', '--python', os.path.join(HERE, 'render.py'), '--', src, prefix,
                    ','.join(VIEWS + DETAIL), '540'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    open(stamp, 'w').write(str(os.path.getmtime(src)))
    return prefix


def stats(path):
    x = np.asarray(Image.open(path).convert('RGBA')).astype(float); m = x[..., 3] > 128
    return int(m.sum()), x[m][:, :3].mean(0)


def tris(model):
    out = []
    for mi in model.mesh_chain():
        out.append({model.doc['materials'][p['material']]['name']: int(model.doc['accessors'][p['indices']]['count'] // 3)
                    for p in model.doc['meshes'][mi]['primitives']})
    return out


res = {}
for tag in MODELS:
    prefix = render(tag)
    lods = {}
    for lod in range(4):
        per = {}
        for v in VIEWS if lod < 3 else ['eye']:
            px, mean = stats(f'{prefix}_LOD{lod}_{v}.png')
            per[v] = {'px': px, 'mean': mean.round(2).tolist()}
        lods[lod] = per
    od = overdraw.analyse(MODELS[tag], 384, os.path.join(W, 'heat', tag))
    layers = {}
    for lod in range(3):
        vs = [od[f'LOD{lod}_{w}'] for w in ('front', 'three_quarter', 'side')]
        layers[lod] = {'all': round(sum(x['layers_mean'] for x in vs) / 3, 2),
                       'front': round(sum(x['front_mean'] for x in vs) / 3, 2),
                       'p95': max(x['layers_p95'] for x in vs),
                       # share of the silhouette where bark or shell is the front surface (no card in front)
                       'opaque_seen': round(sum(x['opaque_seen_px'] / (x['covered_px'] + x['opaque_only_px']) for x in vs) / 3, 3)}
    res[tag] = {'lods': lods, 'layers': layers, 'tris': tris(glb.read(MODELS[tag]))}

report = {'id': tid, 'gates': {}}
ok = True
lines = []
for lod in range(3):
    a = res['inst']['lods'][lod]; b = res['new']['lods'][lod]
    cov = np.mean([b[v]['px'] / a[v]['px'] - 1 for v in VIEWS])
    col = np.mean([np.array(b[v]['mean']) - np.array(a[v]['mean']) for v in VIEWS], 0)
    dcol = float(np.abs(col).max())
    worst_cov = max(abs(b[v]['px'] / a[v]['px'] - 1) for v in VIEWS)
    g = {'coverage': round(float(cov), 4), 'coverage_worst_view': round(float(worst_cov), 4),
         'colour_delta': np.round(col, 2).tolist(), 'colour_max': round(dcol, 2)}
    passed = abs(cov) <= 0.03 and dcol <= 3.0
    ok &= passed
    report['gates'][f'LOD{lod}'] = g
    lines.append(f"LOD{lod} coverage {cov * 100:+.1f} % (worst view {worst_cov * 100:.1f} %), colour "
                 f"{np.round(col, 1).tolist()} max {dcol:.1f} -> {'PASS' if passed else 'FAIL'}")
steps = {}
for tag in MODELS:
    e = [res[tag]['lods'][l]['eye'] for l in range(4)]
    steps[tag] = [{'colour': round(float(np.abs(np.array(e[l + 1]['mean']) - np.array(e[l]['mean'])).max()), 2),
                   'coverage': round(e[l + 1]['px'] / e[l]['px'] - 1, 4)} for l in range(3)]
report['steps'] = steps
for l in range(3):
    s_new, s_old = steps['new'][l], steps['inst'][l]
    passed = s_new['colour'] <= max(4.0, s_old['colour'] + 1.0) and abs(s_new['coverage']) <= max(0.05, abs(s_old['coverage']) + 0.005)
    ok &= passed
    lines.append(f"step LOD{l}->{l + 1} colour {s_new['colour']:.1f} (installed {s_old['colour']:.1f}), coverage "
                 f"{s_new['coverage'] * 100:+.1f} % (installed {s_old['coverage'] * 100:+.1f} %) -> {'PASS' if passed else 'FAIL'}")
for lod in range(3):
    ti, tn = sum(res['inst']['tris'][lod].values()), sum(res['new']['tris'][lod].values())
    li, ln = res['inst']['layers'][lod], res['new']['layers'][lod]
    target = 2.0 if lod == 2 else 3.0
    passed = tn <= ti
    ok &= passed
    lines.append(f"LOD{lod} layers {li['all']:.2f} (front {li['front']:.2f}) -> {ln['all']:.2f} (front {ln['front']:.2f}, "
                 f"p95 {ln['p95']:.0f}) target ~{target}; opaque seen {li['opaque_seen'] * 100:.0f} -> {ln['opaque_seen'] * 100:.0f} %; tris {ti} -> {tn} {res['new']['tris'][lod]} "
                 f"{'' if passed else 'FAIL (more triangles)'}")
report['layers'] = {t: res[t]['layers'] for t in MODELS}; report['tris'] = {t: res[t]['tris'] for t in MODELS}
report['renders'] = {t: res[t]['lods'] for t in MODELS}
# black-patch check (2026-10-16, coordinator): from next to the trunk looking up 60 degrees and a low three-quarter
# view, the share of opaque pixels darker than luminance 12 (sRGB) may not grow beyond the original's + 0.5 %
# ('inst' = work/<id>/installed.glb, the source as it was before this pass; also in backup_pre_overdraw/)
dark = {}
for v in ('up', 'low3q'):
    fr = {}
    for tag in MODELS:
        x = np.asarray(Image.open(os.path.join(W, 'r', f'{tag}_LOD0_{v}.png')).convert('RGBA')).astype(float)
        msk = x[..., 3] > 128
        lum = (0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2])[msk]
        fr[tag] = float((lum < 12).mean()) if msk.any() else 0.0
    dark[v] = fr
    passed = fr['new'] <= fr['inst'] + 0.005
    ok &= passed
    lines.append(f"dark pixels ({v}) original {fr['inst'] * 100:.2f} -> {fr['new'] * 100:.2f} % -> {'PASS' if passed else 'FAIL'}")
report['dark'] = dark
report['pass'] = bool(ok)
json.dump(report, open(os.path.join(W, 'gate.json'), 'w'), indent=1)
for line in lines:
    print('GATE', tid, line)
print('GATE', tid, 'ALL PASS' if ok else 'SOME FAIL (see above)')

# ---------------------------------------------------------------- sheet
BG = (150, 160, 175)


def tile(path, h):
    im = Image.open(path).convert('RGBA')
    im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
    out = Image.new('RGBA', im.size, BG + (255,)); out.alpha_composite(im)
    return out.convert('RGB')


def block(tag, title):
    p = os.path.join(W, 'r', tag)
    row1 = [tile(f'{p}_LOD0_{v}.png', 360) for v in VIEWS] + [tile(f'{p}_LOD{l}_eye.png', 360) for l in (1, 2, 3)]
    row2 = [tile(f'{p}_LOD0_{v}.png', 360) for v in DETAIL]
    hp = os.path.join(W, 'heat', tag)
    row2 += [tile(f'{hp}_all_LOD{l}_front.png', 360) for l in (0, 1, 2)]
    w = max(sum(i.width for i in row1), sum(i.width for i in row2))
    img = Image.new('RGB', (w, 30 + 360 + 22 + 360), BG); dr = ImageDraw.Draw(img)
    dr.text((6, 8), title, fill=(0, 0, 0))
    x = 0
    for i, lab in zip(row1, ['LOD0 eye', 'LOD0 three-quarter', 'LOD0 side', 'LOD1 eye', 'LOD2 eye', 'impostor']):
        img.paste(i, (x, 30)); dr.text((x + 4, 32), lab, fill=(0, 0, 0)); x += i.width
    x = 0
    L = res[tag]['layers']
    labs = ['close', 'under the crown', 'trunk', 'up 60 deg by the trunk', 'low three-quarter'] + [f"layers LOD{l} (front view) mean {L[l]['all']}, in front of opaque {L[l]['front']}"
                                                  for l in (0, 1, 2)]
    for i, lab in zip(row2, labs):
        img.paste(i, (x, 30 + 360 + 22)); dr.text((x + 4, 30 + 360 + 6), lab, fill=(0, 0, 0)); x += i.width
    return img


t_i = ' / '.join(str(sum(t.values())) for t in res['inst']['tris'])
t_n = ' / '.join(str(sum(t.values())) for t in res['new']['tris'])
blocks = [block('inst', f'BEFORE (installed) {spec["glb"]}  triangles {t_i}'),
          block('new', f'AFTER (crown shell, fewer cards)  triangles {t_n}   ' +
                '  '.join(f"LOD{l}: cov {report['gates'][f'LOD{l}']['coverage'] * 100:+.1f} % col {report['gates'][f'LOD{l}']['colour_max']}"
                          for l in range(3)))]
w = max(b.width for b in blocks)
sheet = Image.new('RGB', (w, sum(b.height for b in blocks) + 10), BG); y = 0
for b in blocks:
    sheet.paste(b, (0, y)); y += b.height + 10
sheet.save(os.path.join(R, 'before_after.png'))
print('SHEET', os.path.join(R, 'before_after.png'))
