"""Head-set UV triangles of work/master.blend -> work/head_uv.json: [{"kind": 0 hide | 1 maw inner | 2 maw outer,
"uv": [[u, v] x 3], "co": rest-pose positions}], plus the maw island centre and radius from work/master.json (for compose_head.py)."""
import json
import os

import bmesh
import bpy

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'master.blend'))
mesh = bpy.data.objects['Bld']
bm = bmesh.new()
bm.from_mesh(mesh.data)
bmesh.ops.triangulate(bm, faces=bm.faces[:])
uv = bm.loops.layers.uv.active
head = bm.faces.layers.int['head']
kind = bm.faces.layers.int['maw_kind']
tris = [{'kind': f[kind], 'uv': [[l[uv].uv.x, l[uv].uv.y] for l in f.loops], 'co': [list(l.vert.co) for l in f.loops]}
        for f in bm.faces if f[head]]
info = json.load(open(os.path.join(HERE, 'work', 'master.json')))
json.dump({'tris': tris, 'maw_uv_centre': info['maw_uv_centre'], 'maw_uv_radius': info['maw_uv_radius']},
          open(os.path.join(HERE, 'work', 'head_uv.json'), 'w'))
print('DUMPED', len(tris))
