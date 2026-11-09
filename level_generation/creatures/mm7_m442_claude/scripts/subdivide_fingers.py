"""G5: one smooth subdivision of the fingers and thumb of the sword (right) hand (curled low-poly fingers folded into shards in
the fist; humanoid playbook "low-poly fingers facet when curled"). Faces whose vertices all carry finger weight
(label > 0 from finger_weights.py) are subdivided once in edit mode, which interpolates the vertex groups; the
'finger' label of the new vertices is re-derived from their strongest finger bone. Args: -- <in blend> <out blend>"""
import bpy, bmesh, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body = bpy.data.objects['Body']; me = body.data
before = sum(len(p.vertices) - 2 for p in me.polygons)
lab = np.zeros(len(me.vertices), np.int32); me.attributes['finger'].data.foreach_get('value', lab)
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.context.view_layer.objects.active = body
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_mode(type='FACE'); bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.object.mode_set(mode='OBJECT')
n = 0
for p in me.polygons:
    # right (sword) hand only (character right = -X): the left hand stays relaxed and open
    p.select = all(lab[v] > 0 for v in p.vertices) and me.vertices[p.vertices[0]].co.x < 0
    n += p.select
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.subdivide(number_cuts=1, smoothness=1.0)
bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
bpy.ops.object.mode_set(mode='OBJECT')
me = body.data
# labels for every vertex from the strongest finger chain (0 hand/other, 1..5 thumb..pinky)
gi = {g.index: g.name for g in body.vertex_groups}
lab = np.zeros(len(me.vertices), np.int32)
for v in me.vertices:
    best, bw = 0, 0.0
    for e in v.groups:
        nm = gi[e.group]
        if '_Finger' in nm and e.weight > bw:
            bw = e.weight; best = int(nm.split('_Finger')[1][0]) + 1
    lab[v.index] = best if bw > 0.3 else 0
me.attributes['finger'].data.foreach_set('value', lab.tolist())
print('SUBDIV fingers: faces', n, 'tris', before, '->', sum(len(p.vertices) - 2 for p in me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
