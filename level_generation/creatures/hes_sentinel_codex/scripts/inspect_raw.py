"""Workbench views of a mesh GLB (untextured): three-quarter, left (front to image left), front, back, top; prints
the bounds, triangle count and connected-component sizes. Args: -- <glb> <out prefix> [wire]"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
src, prefix = os.path.abspath(args[0]), os.path.abspath(args[1])
wire = len(args) > 2 and args[2] == 'wire'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
centre, size = (lo + hi) / 2, hi - lo
tris = 0
for o in meshes:
    bm = bmesh.new(); bm.from_mesh(o.data)
    tris += sum(len(f.verts) - 2 for f in bm.faces)
    seen, comps = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, n = [v], 0
        seen.add(v.index)
        while stack:
            w = stack.pop(); n += 1
            for e in w.link_edges:
                u = e.other_vert(w)
                if u.index not in seen:
                    seen.add(u.index); stack.append(u)
        comps.append(n)
    comps.sort(reverse=True)
    print('MESH', o.name, 'verts', len(bm.verts), 'components', len(comps), 'largest', comps[:12])
    bm.free()
print('BOUNDS', [round(x, 3) for x in lo], [round(x, 3) for x in hi], 'size', [round(x, 3) for x in size], 'tris', tris)

scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (0.8, 0.8, 0.78)
scene.display.shading.show_cavity = True
scene.render.resolution_x, scene.render.resolution_y = 900, 900
scene.render.film_transparent = False
if wire:
    for o in meshes:
        m = o.modifiers.new('w', 'WIREFRAME'); m.thickness = 0.002 * max(size); m.use_replace = False
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
scene.collection.objects.link(cam); scene.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = max(size) * 1.15
r = max(size) * 3
views = {'34': (-35, 15), 'left': (-90, 0), 'front': (0, 0), 'back': (180, 0), 'right': (90, 0), 'top': (0, 89)}
# glTF import: the asset's front (+Z glTF) is Blender -Y; azimuth 0 looks from -Y (front)
for name, (az, el) in views.items():
    a, e = math.radians(az), math.radians(el)
    d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    cam.location = centre + d * r
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = f'{prefix}_{name}.png'
    bpy.ops.render.render(write_still=True)
print('VIEWS', prefix)
