#!/usr/bin/env python3
"""Review viewer (review/viewer/): per tier, the installed viewer GLB of the reduced warrior (tier ramps baked, sword
on Socket_Sword, from ../mm8_m404_reduce_claude/review/viewer/) and a copy whose Walking channels are replaced by the
new export's. Writes manifest.json with sha256 and cache-busting ?v= for every model. Usage: viewer_build.py"""
import hashlib, json, shutil, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
from glb_io import Glb
SRC = HERE.parent / 'mm8_m404_reduce_claude/review/viewer'; V = HERE / 'review/viewer'
new = Glb(str(HERE / 'export/mm8_m404.glb')); nch = new.channels('Walking')
TIERS = {'a': 'Lizardman Soldier — green', 'b': 'Lizardman Sergeant — blue', 'c': 'Lizardman Captain — red'}
models = []
for t, label in TIERS.items():
    inst = V / f'mm8_m404_{t}_installed.glb'; shutil.copyfile(SRC / f'mm8_m404_{t}_r80.glb', inst)
    g = Glb(str(inst)); written = 0
    for key, (s, out) in g.channels('Walking').items():
        vals = new.read(nch[key][1])
        if vals.shape == g.read(out).shape:
            g.write(out, vals); written += 1
    g.save(str(V / f'mm8_m404_{t}_walk.glb'))
    for kind, name in (('installed', inst.name), ('new walk', f'mm8_m404_{t}_walk.glb')):
        sha = hashlib.sha256((V / name).read_bytes()).hexdigest()
        models.append({'id': f'm404_{t}_' + ('installed' if kind == 'installed' else 'walk'),
                       'label': f'{label} · {kind}', 'url': f'{name}?v={sha[:12]}', 'sha256': sha,
                       'revision': 'walk-1'})
    print(t, 'Walking channels written', written)
m = json.loads((SRC / 'manifest.json').read_text())
m.update(revision='walk-1', default_clip='Walking', default_model='m404_a_walk', models=models,
         feedback='../feedback/user_feedback.json')
if 'Walking' in m.get('clips', {}):
    m['clips']['Walking']['provenance'] = ('New full-body walk (mm8_m404_walk_claude): hips turn and roll, chest '
                                           'counter-turns, pelvis bob and sway, heel-to-toe roll at 1.45 m stride.')
(V / 'manifest.json').write_text(json.dumps(m, indent=1))
