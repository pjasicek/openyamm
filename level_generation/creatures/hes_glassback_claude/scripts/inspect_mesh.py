"""Import the Meshy Smart Topology return, report bbox/components, render orthographic views with a 10 cm grid.
Args: -- <glb> <out prefix>"""
import bpy, sys, os
import bmesh
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C

args = sys.argv[sys.argv.index('--') + 1:]
glb, out = args[:2]
rotz = float(args[2]) if len(args) > 2 else 0.0
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
import math
for o in meshes:
    o.matrix_world = Matrix.Rotation(math.radians(rotz), 4, 'Z') @ o.matrix_world
for o in meshes:
    me = o.data
    co = np.array([tuple(o.matrix_world @ v.co) for v in me.vertices])
    print('MESH', o.name, 'verts', len(me.vertices), 'faces', len(me.polygons), 'tris',
          sum(len(p.vertices) - 2 for p in me.polygons))
    print('BBOX min', co.min(0).round(3), 'max', co.max(0).round(3))
    bm = bmesh.new(); bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    seen = set(); comps = []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack = [v]; comp = []
        seen.add(v.index)
        while stack:
            a = stack.pop(); comp.append(a.index)
            for e in a.link_edges:
                b = e.other_vert(a)
                if b.index not in seen:
                    seen.add(b.index); stack.append(b)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    for i, c in enumerate(comps[:12]):
        p = co[c]
        print('COMP', i, len(c), 'min', p.min(0).round(3), 'max', p.max(0).round(3))
    print('COMPONENTS', len(comps))
co = np.concatenate([np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices]) for o in meshes])
c = (co.min(0) + co.max(0)) / 2
ext = (co.max(0) - co.min(0)).max() * 1.15
# grid
import bmesh as B
bm = B.new()
for k in range(-20, 21):
    for axis in range(3):
        pass
for view, d in (('front', (0, -1, 0)), ('side', (1, 0, 0)), ('top', (0, 0, 1)), ('quarter', (0.7, -0.7, 0.35))):
    loc = Vector(c) + Vector(d).normalized() * 10
    C.render_ortho(loc, c, ext, f'{out}_{view}.png')
