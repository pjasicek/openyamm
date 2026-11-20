"""Baseline for parts_gate.py: the accepted candidate (work/ladder.blend Cand_55) with its original Meshy teeth and
spikes labelled like build_parts.py (part 4 spike, 5 tooth) -> work/baseline.blend (object Rebuilt).
Usage: blender -b -P baseline_parts.py"""
import json, os, bpy
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
c = bpy.data.objects['Cand_55']; me = c.data
probe = json.load(open(os.path.join(HERE, 'work', 'parts_probe.json')))
n = len(me.vertices); parent = np.arange(n)


def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]; i = parent[i]
    return i
for e in me.edges:
    a, b = find(e.vertices[0]), find(e.vertices[1])
    if a != b:
        parent[a] = b
lab = np.unique([find(i) for i in range(n)], return_inverse=True)[1]
eyes = [p for p in probe if p['faces'] > 90 and p['length'] < .012]
wings = {p['piece'] for p in probe if p['faces'] > 150}
mouth = {p['piece'] for p in probe if p['bone'] == 'Jaw' and p['length'] > .03}
teeth = {p['piece'] for p in probe if p['centre'][1] < -.435 and p['length'] < .008 and p not in eyes}
spikes = {p['piece'] for p in probe} - wings - mouth - teeth - {p['piece'] for p in eyes}
attr = me.attributes.new('part', 'INT', 'FACE')
for p in me.polygons:
    l = lab[p.vertices[0]]
    attr.data[p.index].value = 1 if l in wings else 2 if l in {e['piece'] for e in eyes} else 3 if l in mouth else \
        4 if l in spikes else 5 if l in teeth else 0
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not c:
        bpy.data.objects.remove(o, do_unlink=True)
c.name = 'Rebuilt'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'baseline.blend'))
print('BASELINE', len(teeth), 'teeth', len(spikes), 'spikes')
