"""Repair confirmed Smart Topology artifacts before rigging; preserve the raw return."""
from pathlib import Path
import json
import sys
import bpy
from mathutils import Vector
import numpy as np

p = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(p / 'scripts'))
import common
bpy.ops.wm.open_mainfile(filepath=str(p / 'work/st_v1_parts.blend'))
parts = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
assert len(parts) == 92 and len(parts['P00'].data.vertices) == 5726
# Meshy joined the whiskers into a heavy closed loop, disconnected from the muzzle.
bpy.data.objects.remove(parts.pop('P02'), do_unlink=True)
bpy.data.objects.remove(parts.pop('P91'), do_unlink=True)
main = parts['P00']
co = np.array([tuple(v.co) for v in main.data.vertices])
# Shorten the free tail about its measured root, blending at the root to retain its attachment.
tail = (co[:, 1] > -0.30) & (co[:, 2] < 0.94)
y = co[tail, 1]
dy = y + 0.30
transition = 0.12
t = np.clip(dy / transition, 0, 1)
# Integrate a smooth speed change: the tail centreline stays monotone at its root.
shortened = np.where(dy < transition, transition * (t**3 - 0.5*t**4), dy - 0.5*transition)
co[tail, 1] -= 0.38 * shortened
centre_z = np.interp(y, [-0.30,-0.27,-0.15,-0.05,0.05,0.15,0.25,0.35,0.55,0.84],
                    [0.90,0.81,0.61,0.465,0.371,0.297,0.241,0.212,0.169,0.155])
co[tail, 2] += 0.38 * (0.90 - centre_z) * (t*t*(3-2*t))
main.data.vertices.foreach_set('co', co.ravel())
# Centre the ankles, not the full bounding box extended by the tail.
ankles = co[(co[:,2] > 0.11) & (co[:,2] < 0.17) & (co[:,1] < -0.35)]
centre = np.array([(ankles[:,0].min()+ankles[:,0].max())/2, (ankles[:,1].min()+ankles[:,1].max())/2, 0.0])
for o in parts.values():
    for v in o.data.vertices:
        v.co -= Vector(centre)
    attr = o.data.attributes.new('piece', 'INT', 'POINT')
    attr.data.foreach_set('value', [int(o.name[1:])] * len(o.data.vertices))
    o.data.materials.clear()
    o.select_set(True)
bpy.context.view_layer.objects.active = main
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = body.data.name = 'Body'
co = np.array([tuple(v.co) for v in body.data.vertices])
body.data.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', co.ravel())
assert np.isfinite(co).all() and abs(co[:,2].min()) < 1e-5
scene = bpy.context.scene
common.workbench_clay(scene)
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (0.65, 0.65, 0.65)
bpy.ops.wm.save_as_mainfile(filepath=str(p / 'work/step1.blend'))
common.render_views(str(p / 'review/body_clean'), 0.85, 1.95,
                    views=('front','three_quarter','left','back'),resolution=(1000,1000))
common.render_views(str(p / 'review/head_clean'), 1.5, 0.55,
                    views=('front','three_quarter'),resolution=(600,600),target=(0,-0.05))
# A provisional material/UV satisfies Meshy's rigging input; final UVs follow weighting/reduction.
mat = bpy.data.materials.new('Provisional');mat.use_nodes=True
image = bpy.data.images.new('provisional', width=2, height=2)
image.pixels[:] = [0.5,0.5,0.5,1.0] * 4
node = mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image
mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
body.data.materials.append(mat)
if not body.data.uv_layers:body.data.uv_layers.new(name='UVMap')
for o in bpy.data.objects:o.select_set(o == body)
(p/'export').mkdir(exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(p/'export/body_for_rig.glb'),use_selection=True,
                         export_format='GLB',export_animations=False,export_skins=False,export_attributes=False)
print('CLEANUP',len(co),'vertices',sum(len(f.vertices)-2 for f in body.data.polygons),'triangles',int(tail.sum()),'tail vertices')
(p/'work/cleanup.json').write_text(json.dumps({'source':'work/st_v1_parts.blend','removed_whisker_loop_piece':2,
    'removed_isolated_triangle_piece':91,'tail_free_length_scale':0.62,'origin_shift':centre.tolist()},indent=2)+'\n')
