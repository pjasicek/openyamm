"""UVs of the grafted, reduced hydra (rest pose) and the body retexture upload.
- Body and lofts (face attribute part 0): Smart UV Project at 66 degrees, packed into 0..1 of the body texture
  (layer 'UVMap'); exported alone as texturing/body_upload.glb (neutral, unrigged) for the Meshy retexture with
  enable_original_uv.
- Heads (part k): their own unwraps (layer 'HeadUV', the retextured texturing/head<k>_upload.glb layout) mapped into
  tile k of the head atlas (HEAD_COLS x HEAD_ROWS tiles, tile k at column (k-1) % HEAD_COLS, row (k-1) // HEAD_COLS
  from the top) in 'UVMap'; compose_hydra.py builds the atlas image with the same rule.
Args: -- <in blend> <out blend>"""
import bpy, bmesh, os, sys, math
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEAD_COLS, HEAD_ROWS = 3, 2
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
ob = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; me = ob.data
rig.animation_data_create(); rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
part = np.zeros(len(me.polygons), np.int32); me.attributes['part'].data.foreach_get('value', part)
if 'UVMap' not in me.uv_layers:
    me.uv_layers.new(name='UVMap')
for layer in list(me.uv_layers):
    if layer.name not in ('UVMap', 'HeadUV'):
        me.uv_layers.remove(layer)
me.uv_layers.active = me.uv_layers['UVMap']
bpy.context.view_layer.objects.active = ob
for o in bpy.data.objects:
    o.select_set(o == ob)
for p in me.polygons:
    p.select = bool(part[p.index] == 0)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_mode(type='FACE')
bpy.ops.mesh.hide(unselected=True)
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004, area_weight=0.0, scale_to_bounds=False)
bpy.ops.uv.pack_islands(margin=0.004, rotate=True)
bpy.ops.mesh.reveal(); bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.object.mode_set(mode='OBJECT')
uv = me.uv_layers['UVMap'].data; huv = me.uv_layers['HeadUV'].data
for p in me.polygons:
    k = int(part[p.index])
    if k <= 0:
        continue
    col, row = (k - 1) % HEAD_COLS, (k - 1) // HEAD_COLS
    for li in p.loop_indices:
        u, v = huv[li].uv
        uv[li].uv = ((col + u) / HEAD_COLS, (HEAD_ROWS - 1 - row + v) / HEAD_ROWS)
me.uv_layers.active = me.uv_layers['UVMap']
for layer in me.uv_layers:
    layer.active_render = layer.name == 'UVMap'
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
# body upload: part-0 faces only, UVMap only, no rig
os.makedirs(os.path.join(HERE, 'texturing'), exist_ok=True)
dup = ob.copy(); dup.data = me.copy(); dup.modifiers.clear(); dup.parent = None; dup.vertex_groups.clear()
bpy.context.scene.collection.objects.link(dup)
bm = bmesh.new(); bm.from_mesh(dup.data); pl = bm.faces.layers.int.get('part')
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[pl] != 0], context='FACES')
bm.to_mesh(dup.data); bm.free()
dup.data.uv_layers.remove(dup.data.uv_layers['HeadUV'])
for at in [a.name for a in dup.data.attributes if a.name in ('piece', 'orig_co', 'chain_owner', 'part', 'loft_s', 'loft_ref')]:
    dup.data.attributes.remove(dup.data.attributes[at])
dup.data.materials.clear(); dup.data.materials.append(bpy.data.materials.new('HydraBody'))
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'texturing', 'body_upload.glb'), use_selection=True,
                          export_format='GLB', export_yup=True, export_texcoords=True, export_normals=True,
                          export_materials='PLACEHOLDER', export_skins=False, export_animations=False)
print('UV body faces', int((part == 0).sum()), 'head faces', int((part > 0).sum()),
      'upload triangles', sum(len(p.vertices) - 2 for p in dup.data.polygons))
