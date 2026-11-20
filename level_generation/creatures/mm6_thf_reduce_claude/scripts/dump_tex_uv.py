"""Triangles of work/master_tex.blend per texture set -> work/tex_uv.json: {"regions": [names], "parts": [names],
"tris": [{"set": 0 body | 1 cloak | 2 head, "part": i, "region": i, "uv": [[u, v] x 3]}]} (for compose_tex.py)."""
import json
import os

import bmesh
import bpy

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'master_tex.blend'))
mesh = bpy.data.objects['Thief']
sc = bpy.context.scene
bm = bmesh.new()
bm.from_mesh(mesh.data)
bmesh.ops.triangulate(bm, faces=bm.faces[:])
uv = bm.loops.layers.uv.active
L = {n: bm.faces.layers.int[n] for n in ('tex_set', 'part', 'uv_region')}
tris = [{'set': f[L['tex_set']], 'part': f[L['part']], 'region': f[L['uv_region']],
         'uv': [[l[uv].uv.x, l[uv].uv.y] for l in f.loops]} for f in bm.faces]
json.dump({'regions': json.loads(sc['thf_uv_regions']), 'parts': json.loads(sc['thf_parts']), 'tris': tris},
          open(os.path.join(HERE, 'work', 'tex_uv.json'), 'w'))
print('DUMPED', len(tris))
