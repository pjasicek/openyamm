"""Dump MM9 dragon mesh stats: influences per vertex, wing (Y*) vertex/face counts and positions (bind, lifted)."""
import bpy, sys, json
from collections import Counter
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
out = {}
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    me = o.data
    infl = Counter(len([g for g in v.groups if g.weight > 0.001]) for v in me.vertices)
    wing = [v.index for v in me.vertices if any(o.vertex_groups[g.group].name.startswith('Y') for g in v.groups)]
    ws = set(wing)
    wf = [p for p in me.polygons if all(i in ws for i in p.vertices)]
    pos = sorted({tuple(round(c, 3) for c in (o.matrix_world @ me.vertices[i].co)) for i in wing})
    out[o.name] = {'verts': len(me.vertices), 'influences': dict(infl), 'wing_verts': len(wing), 'wing_faces': len(wf),
                   'wing_unique_pos': len(pos), 'wing_pos_left': [p for p in pos if p[0] < 0]}
print('DUMP ' + json.dumps(out))
