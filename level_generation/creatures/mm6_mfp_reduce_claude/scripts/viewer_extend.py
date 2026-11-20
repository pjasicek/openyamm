#!/usr/bin/env python3
"""Extend the reduction viewer manifest (viewer_manifest.py) for the cutpurse review: per-model clip durations (the
installed Attack is 1.125 s, the new stab 1.3 s), the unreduced round-3 model with the new Attack ('stab' tag), the knife
attached at the Knife joint (installed knife on installed models, reduced knife on the reduced pick), Attack provenance.
Usage: viewer_extend.py <pick tag> <pick tris>"""
import hashlib, json, re, struct, sys
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review/viewer'
tag, ptris = sys.argv[1], int(sys.argv[2])
m = json.loads((V / 'manifest.json').read_text())


def durations(path):
    b = path.read_bytes(); n = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + n])
    return {a['name']: round(max(j['accessors'][s['input']]['max'][0] for s in a['samplers']), 6) for a in j['animations']}


def knife(name):
    h = hashlib.sha256((V / name).read_bytes()).hexdigest()[:12]
    return [{'url': f'{name}?v={h}', 'node': 'Knife'}]


models = []
for x in m['models']:
    variant, t = re.match(r'(.*)_(r100|' + re.escape(tag) + ')$', x['id']).groups()
    f = V / x['url'].split('?')[0]
    x['durations'] = durations(f)
    if t == 'r100':
        x['label'] = f'{variant} · installed (old attack) · 10,183 tris'; x['attachments'] = knife('knife_installed.glb')
        models.append(x)
        g = V / f'mm6_{variant}_stab.glb'; h = hashlib.sha256(g.read_bytes()).hexdigest()
        models.append({'id': f'{variant}_stab', 'label': f'{variant} · installed + new stab · 10,183 tris',
                       'url': f'{g.name}?v={h[:12]}', 'revision': x['revision'], 'sha256': h,
                       'durations': durations(g), 'attachments': knife('knife_installed.glb')})
    else:
        x['label'] = f'{variant} · reduced {tag} + new stab · {ptris:,} tris, knife 1,895'; x['attachments'] = knife('knife_reduced.glb')
        models.append(x)
m['models'] = models
m['model'] = 'MM6 Cutpurse — new dagger stab + reduction'
m['clips']['Attack']['provenance'] = ('new: Mixamo "Stabbing (1)" (right-hand stab), legs planted, wind-up/thrust/hold, '
                                      'blended from/to Standing, wrist bend <= 30 deg; installed models keep the old attack')
(V / 'manifest.json').write_text(json.dumps(m, indent=1))
print('EXTENDED', [x['id'] for x in models])
