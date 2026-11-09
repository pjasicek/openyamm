"""Quick look at a species' Sapling skeleton: every spline as a bevelled tube (no leaves), front and side
orthographic silhouettes against the family's bare and summer sprites (work/<id>/skeleton.png). Tuning aid for the
bare winter state, which shows the skeleton the leafy seasons hide. Usage: blender --background --python
skeleton_preview.py -- <id> [bare sprite stem]"""
import bpy, os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
spec = common.load(); W = spec['work']; H = spec['height_m']
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.curve.tree_add(do_update=True, bevel=True, showLeaves=False, useArm=False, prune=False, **spec['sapling'])
tree = bpy.data.objects['tree']
sc = bpy.context.scene
for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        sc.render.engine = engine; break
    except TypeError:
        continue
sc.render.film_transparent = True; sc.render.resolution_x = sc.render.resolution_y = 512
m = bpy.data.materials.new('k'); m.use_nodes = True
nt = m.node_tree; out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.25, 0.12, 0.05, 1)
nt.links.new(em.outputs[0], out.inputs['Surface'])
tree.data.materials.append(m)
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = H
top = max(p.co.z for s in tree.data.splines for p in s.bezier_points)
reach = max(math.hypot(p.co.x, p.co.y) for s in tree.data.splines for p in s.bezier_points)
print('SKELETON top', round(top, 2), 'reach', round(reach, 2), 'height_m', H, 'splines', len(tree.data.splines))
import json
json.dump({'top': top, 'reach': reach, 'scale': spec['sapling']['scale']}, open(os.path.join(W, 'skel.json'), 'w'))
for view, (loc, rot) in {'front': ((0, -30, H / 2), (math.pi / 2, 0, 0)),
                         'side': ((30, 0, H / 2), (math.pi / 2, 0, math.pi / 2))}.items():
    cam.location = loc; cam.rotation_euler = rot
    sc.render.filepath = os.path.join(W, f'skel_{view}.png'); bpy.ops.render.render(write_still=True)
