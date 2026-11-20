#!/usr/bin/env python3
"""Grade a bare tree's bark (and twig colours) to its native sprite: the linear ratio of the sprite's mean colour to
the LOD0 eye render's (the REVIEW line of work/<id>.build.log) scales species bark.target_srgb and the twig colours.
Run after a build, then rebuild. Usage: grade_bare.py <id> [...]"""
import ast, json, os, re, sys
import numpy as np
import common
for sid in sys.argv[1:]:
    line = [l for l in open(os.path.join(common.TREES, 'work', f'{sid}.build.log')) if l.startswith('REVIEW')][-1]
    sprite, eye = [ast.literal_eval(m)[0] for m in re.findall(r'\(\[.*?\], \[.*?\]\)', line)]
    ratio = common.lin(np.array(sprite) / 255.0) / common.lin(np.array(eye) / 255.0)
    path = os.path.join(common.TREES, 'species', f'{sid}.json'); d = json.load(open(path))

    def scaled(c):
        return [int(v) for v in np.clip(np.round(common.srgb(common.lin(np.array(c) / 255.0) * ratio) * 255), 0, 255)]
    spec = common.load(sid)
    d.setdefault('bark', {})['target_srgb'] = scaled(spec['bark']['target_srgb'])
    for key in ('twig_srgb', 'twig_highlight_srgb'):
        d['bare'][key] = scaled(spec['bare'][key])
    json.dump(d, open(path, 'w'), indent=1)
    print('GRADE', sid, 'sprite', sprite, 'eye', eye, 'ratio', ratio.round(3).tolist(), 'bark ->', d['bark']['target_srgb'])
