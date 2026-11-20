"""Weld the skin's unwelded seams (review 2: light/dark triangles on the neck were open seams from Smart Topology:
duplicate vertices made neighbouring faces shade with different normals). Skin vertices (piece 0) closer than DIST are
merged (bmesh remove_doubles keeps one vertex's weights; loop UVs are kept). In place on <blend>. Args: -- <blend>"""
import bpy, bmesh, sys, os
import numpy as np
DIST = 2e-4
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1]))
rig = bpy.data.objects['Rig']; rig.animation_data_create(); rig.animation_data.action = None
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
pl = bm.verts.layers.int['piece']
skin = [v for v in bm.verts if v[pl] == 0]
before = len(bm.verts)
bnd0 = sum(1 for e in bm.edges if e.is_boundary and all(v[pl] == 0 for v in e.verts))
bmesh.ops.remove_doubles(bm, verts=skin, dist=DIST)
bnd1 = sum(1 for e in bm.edges if e.is_boundary and all(v[pl] == 0 for v in e.verts))
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_mainfile()
print('WELD skin vertices merged', before - len(me.vertices), 'skin boundary edges', bnd0, '->', bnd1)
