"""Prove that only the Walking clip's data changed between two GLBs: every accessor outside Walking's samplers is
byte-identical, and the JSON differs only in those accessors' min/max. Usage: compare_glb.py <a.glb> <b.glb>"""
import sys, os, json, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glb_io import Glb
a, b = Glb(sys.argv[1]), Glb(sys.argv[2])
walk = a.animation('Walking')
mine = {s['output'] for s in walk['samplers']} | {s['input'] for s in walk['samplers']}
changed_outside, changed_walk = [], []
for i in range(len(a.json['accessors'])):
    same = (a.read(i) == b.read(i)).all() if a.json['accessors'][i].get('bufferView') is not None else True
    if not same:
        (changed_walk if i in mine else changed_outside).append(i)
ja, jb = copy.deepcopy(a.json), copy.deepcopy(b.json)
for j in (ja, jb):
    for i in mine:
        j['accessors'][i].pop('min', None); j['accessors'][i].pop('max', None)
names = {s['output']: a.json['nodes'][c['target']['node']]['name'] + '.' + c['target']['path']
         for c in walk['channels'] for s in [walk['samplers'][c['sampler']]]}
print(json.dumps({'json_equal_apart_from_walking_min_max': ja == jb, 'bin_size_equal': len(a.bin) == len(b.bin),
                  'changed_accessors_outside_walking': changed_outside,
                  'changed_walking_channels': sorted(names.get(i, f'input{i}') for i in changed_walk)}, indent=1))
