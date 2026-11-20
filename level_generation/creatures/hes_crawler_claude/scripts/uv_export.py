"""UVs from the xatlas unwrap (work/uv_atlas.npz from uv_dump_mesh.py + uv_atlas.py: 338 charts, 77.5 % of the 2K page,
1018 texels/m, the head charts at 2x), applied per triangle corner; save work/anim_base_uv.blend (-> weights_fix.py -> attachments.py -> work/anim_base.blend, the master anim_hcr.py keys) and export the neutral,
unrigged texturing/hcr_upload_v2.glb for the Meshy retexture. (v1 used Smart UV Project: 821 islands at 27 % coverage of
the page, texturing/hcr_upload_smartuv_v1.glb.)"""
import bpy, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'claude_shared'))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
mesh = bpy.data.objects['Crawler']; rig = bpy.data.objects['Crawler_Rig']
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
for uv in list(mesh.data.uv_layers):
    mesh.data.uv_layers.remove(uv)
mesh.data.uv_layers.new(name='UVMap')
uvs = np.load(os.path.join(HERE, 'work', 'uv_atlas.npz'))['uv']
layer = mesh.data.uv_layers['UVMap'].data
assert len(uvs) == len(mesh.data.polygons)
for p in mesh.data.polygons:
    for k, li in enumerate(p.loop_indices):
        layer[li].uv = tuple(uvs[p.index, k])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'anim_base_uv.blend'))
os.makedirs(os.path.join(HERE, 'texturing'), exist_ok=True)
dup = mesh.copy(); dup.data = mesh.data.copy(); dup.modifiers.clear(); dup.parent = None
bpy.context.scene.collection.objects.link(dup)
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'texturing', 'hcr_upload_v2.glb'), use_selection=True,
                          export_format='GLB', export_yup=True, export_skins=False, export_animations=False,
                          export_materials='NONE')
print('UV done; exported upload')
