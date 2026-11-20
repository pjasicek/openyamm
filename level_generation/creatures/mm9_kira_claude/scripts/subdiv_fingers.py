"""One smooth subdivision of the glove fingers (user review 2026-11-02: "the fingers show hard faceted shading"; humanoid
playbook "low-poly fingers facet when curled", hes_ashrunner_claude/scripts/subdivide_fingers.py). graft_hands.py
decimated each MPFB hand to 760 triangles: 6-sided fingers with 16 deg median / 39 deg p90 dihedrals under smooth
normals. Faces whose every vertex carries finger-bone weight >= MIN (Thumb/Index/Middle/Ring/Pinky groups) are cut once
(smoothness 1); Blender interpolates UVs linearly inside each face (the paint follows), vertex groups and attributes.
Args: <in blend> <out blend> [min 0.3]"""
import bpy, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]; MIN = float(a[2]) if len(a) > 2 else 0.3
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
for o in bpy.data.objects: o.select_set(o == body)
bpy.context.view_layer.objects.active = body
before = len(me.polygons)
fg = {g.index for g in body.vertex_groups if any(k in g.name for k in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')) and not g.name.startswith('MP_')}
fw = np.array([sum(g.weight for g in v.groups if g.group in fg) for v in me.vertices])
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_mode(type='FACE'); bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.object.mode_set(mode='OBJECT')
n = 0
for p in me.polygons:
    p.select = bool(all(fw[v] >= MIN for v in p.vertices)); n += p.select
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.subdivide(number_cuts=1, smoothness=1.0)
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('SUBDIV ' + json.dumps(dict(faces_cut=n, tris_before=before, tris_after=len(me.polygons))))
