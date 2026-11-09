#!/usr/bin/env python3
"""Viewer manifest for the hands/clips/reduction review: per tier the installed model and the new reduced build, each
with its staff attachment on the Staff joint and its own clip durations (the new Attack/Cast are 1.125 s, the new
Death 1.75 s).
Usage: viewer_manifest2.py <new tag> <new tris>"""
import hashlib, json, struct, sys
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review/viewer'
tag, new_tris = sys.argv[1], int(sys.argv[2])


def durations(p):
    raw = p.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; j = json.loads(raw[20:20 + n])
    return {a['name']: round(max(j['accessors'][s['input']]['max'][0] for s in a['samplers']), 6)
            for a in j['animations']}


def h(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


LOOP = ('Standing', 'Walking', 'Running', 'Fidget')
models, clips = [], {}
for tier in ('a', 'b', 'c'):
    for t, label, staff in (('r100', 'installed (old hands and clips) · 10,421 tris', 'staff_installed.glb'),
                            (tag, f'new hands + library Attack/Cast/Death, reduced · {new_tris:,} tris + staff 552',
                             'staff_new.glb')):
        g = V / f'mm6_cle_{tier}_{t}.glb'; d = durations(g)
        for k, v in d.items():
            clips.setdefault(k, {'label': k, 'duration': v, 'mode': 'loop' if k in LOOP else 'once',
                                 'provenance': '', 'anchors': []})
        sh = h(V / staff)
        models.append({'id': f'cle_{tier}_{t}', 'label': f'cle_{tier} · {label}', 'url': f'{g.name}?v={h(g)[:12]}',
                       'revision': 'hands-2', 'sha256': h(g), 'durations': d,
                       'attachments': [{'url': f'{staff}?v={sh[:12]}', 'node': 'Staff'}]})
clips['Attack']['provenance'] = 'new: Mixamo Spell Cast (staff thrust at the target, release 0.54 s)'
clips['Cast']['provenance'] = 'new: Mixamo Spell Cast mirrored (right palm thrust, release 0.54 s)'
clips['Death']['provenance'] = 'new: Mixamo Dying (7) (stagger back, knee, face down), legs settle straight'
manifest = {'revision': 'hands-2', 'model': 'MM6 Cleric — new hands, library Attack/Cast, reduction',
            'default_clip': 'Standing', 'default_model': models[1]['id'], 'feedback': '../feedback/user_feedback.json',
            'clips': clips, 'models': models}
(V / 'manifest.json').write_text(json.dumps(manifest, indent=1))
print('MANIFEST', len(models), 'models', list(clips))
