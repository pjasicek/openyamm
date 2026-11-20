"""HD base: import the four-view Meshy model (hd_multiview_v1, textured with Meshy's own UVs), weld the UV-seam vertex
splits (one closed mesh; UVs stay per corner), move it into the rig frame (feet on the ground, 1.8 m tall, centred on
x, forward -Y) and save work/hd_base.blend with object 'Demon'. The Meshy textures are copied to textures/hd_*.png."""
import bpy, bmesh, os, shutil
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, 'meshy', 'hd_multiview_v1')
HEIGHT = 1.8
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(SRC, 'model_urls_glb.glb'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o is not mesh:
        bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
bpy.context.view_layer.objects.active = mesh; mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bm = bmesh.new(); bm.from_mesh(mesh.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.to_mesh(mesh.data); bm.free()
co = np.array([tuple(v.co) for v in mesh.data.vertices])
s = HEIGHT / (co[:, 2].max() - co[:, 2].min())
mesh.scale = (s, s, s)
bpy.ops.object.transform_apply(scale=True)
co = np.array([tuple(v.co) for v in mesh.data.vertices])
mesh.location = (-(co[:, 0].max() + co[:, 0].min()) / 2, -(co[:, 1].max() + co[:, 1].min()) / 2, -co[:, 2].min())
bpy.ops.object.transform_apply(location=True)
mesh.name = mesh.data.name = 'Demon'
for p in mesh.data.polygons:
    p.use_smooth = True
os.makedirs(os.path.join(HERE, 'textures'), exist_ok=True)
for k in ('base_color', 'normal', 'roughness', 'metallic'):
    shutil.copy(os.path.join(SRC, f'texture_urls_0_{k}.png'), os.path.join(HERE, 'textures', f'hd_{k}.png'))
co = np.array([tuple(v.co) for v in mesh.data.vertices])
print('HD BASE verts', len(co), 'tris', sum(len(p.vertices) - 2 for p in mesh.data.polygons), 'bbox', co.min(0).round(3),
      co.max(0).round(3))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'hd_base.blend'))
