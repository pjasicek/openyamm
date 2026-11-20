"""Puts the Meshy body retexture (meshy/<job>/) on the rigged master for review: work/rig_v7.blend -> review renders
(the master itself is not saved). Checks that the returned model kept our UVs (same positions -> same UVs), builds a
preview material from base colour/normal/roughness/metallic, and renders textured views in the Standing pose.
Args: job."""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
job = sys.argv[sys.argv.index('--') + 1]
D = os.path.join(common.PROJECT, 'meshy', job)
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v6.blend'))
mesh = bpy.data.objects['Guard']
me = mesh.data
arm = bpy.data.objects['Guard_Rig']
arm.animation_data.action = None
for b in arm.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(D, 'model_urls_glb.glb'))
ret = next(o for o in set(bpy.data.objects) - before if o.type == 'MESH')
rme = ret.data
pts = {}
for p in rme.polygons:
    for li in p.loop_indices:
        v = ret.matrix_world @ rme.vertices[rme.loops[li].vertex_index].co
        pts.setdefault((round(v.x, 3), round(v.y, 3), round(v.z, 3)), []).append(tuple(rme.uv_layers.active.data[li].uv))
miss, diff = 0, []
for p in me.polygons:
    for li in p.loop_indices:
        v = mesh.matrix_world @ me.vertices[me.loops[li].vertex_index].co
        k = (round(v.x, 3), round(v.y, 3), round(v.z, 3))
        if k not in pts:
            miss += 1
            continue
        uv = me.uv_layers.active.data[li].uv
        diff.append(min(abs(uv[0] - a) + abs(uv[1] - b) for a, b in pts[k]))
print('UVCHECK loops', len(diff), 'unmatched positions', miss, 'max uv diff', round(max(diff), 5) if diff else None,
      'median', round(float(np.median(diff)), 6) if diff else None)
for o in list(set(bpy.data.objects) - before):
    bpy.data.objects.remove(o, do_unlink=True)
mat = bpy.data.materials.new('GuardPreview')
mat.use_nodes = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')


def tex(name, colorspace):
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(os.path.join(D, name))
    t.image.colorspace_settings.name = colorspace
    return t


nt.links.new(tex('texture_urls_0_base_color.png', 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
me.materials.clear()
me.materials.append(mat)
s = bpy.context.scene
arm.animation_data.action = bpy.data.actions['Standing']
if bpy.data.actions['Standing'].slots:
    arm.animation_data.action_slot = bpy.data.actions['Standing'].slots[0]
s.frame_set(0)
common.workbench_clay(s, textured=True)
common.render_views(os.path.join(common.REVIEW, f'{job}_full'), 0.85, 1.85, views=('front', 'three_quarter', 'left', 'back'),
                    resolution=(500, 700))
common.render_views(os.path.join(common.REVIEW, f'{job}_head'), 1.41, 0.36, views=('front', 'three_quarter', 'left'),
                    resolution=(400, 400))
