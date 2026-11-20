"""Freeze reduced topology and prepare independent body/head texture uploads."""
import bpy,bmesh,sys,os,math,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduced_v1.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;scene=bpy.context.scene
# Restore contact after reduction, baking only the root correction at the final export rate.
ground={}
for a in bpy.data.actions:
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];corrections=[]
 for frame in range(round(a.frame_range[1])+1):
  scene.frame_set(frame);bpy.context.view_layer.update()
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();z=min(v.co.z for v in mesh.vertices);ev.to_mesh_clear()
  pb=rig.pose.bones['B_Pelvis'];m=pb.matrix.copy();m.translation.z-=z;pb.matrix=m
  corrections.append((frame,pb.location.copy(),z))
 for frame,loc,z in corrections:
  rig.pose.bones['B_Pelvis'].location=loc;rig.pose.bones['B_Pelvis'].keyframe_insert('location',frame=frame,group='B_Pelvis')
 ground[a.name]=[min(x[2] for x in corrections),max(x[2] for x in corrections)]
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
hg={body.vertex_groups[n].index for n in ['B_Head','B_Neck']}
hw=np.array([sum(e.weight for e in v.groups if e.group in hg) for v in me.vertices])
head=np.array([int(hw[list(f.vertices)].mean()>.6 and f.center.z>1.98) for f in me.polygons],np.int32)
assert 100<head.sum()<len(head)/3
attr=me.attributes.new('head','INT','FACE');attr.data.foreach_set('value',head)
me.uv_layers[0].name='UVMap'
me.uv_layers.new(name='HeadUV');me.uv_layers.active=me.uv_layers['HeadUV']
for o in bpy.data.objects:o.select_set(o==body)
bpy.context.view_layer.objects.active=body
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_mode(type='FACE');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
for f in me.polygons:f.select=bool(head[f.index])
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012,scale_to_bounds=False);bpy.ops.uv.pack_islands(margin=.012);bpy.ops.object.mode_set(mode='OBJECT')
me.uv_layers.active=me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/texture_ready.blend'))
(P/'work/reduction_ground_correction.json').write_text(json.dumps(ground,indent=2))
def export(which, out, uv):
    ob = body.copy(); ob.data = body.data.copy(); bpy.context.scene.collection.objects.link(ob)
    ob.parent = None; ob.matrix_world = body.matrix_world.copy()
    for m in list(ob.modifiers):
        ob.modifiers.remove(m)
    ob.vertex_groups.clear()
    import bmesh
    bm = bmesh.new(); bm.from_mesh(ob.data); hl = bm.faces.layers.int['head']
    if which == 'head':
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[hl] == 0], context='FACES')
    bm.to_mesh(ob.data); bm.free()
    for l in [l.name for l in ob.data.uv_layers if l.name != uv]:
        ob.data.uv_layers.remove(ob.data.uv_layers[l])
    for at in [x.name for x in ob.data.attributes if x.name in ('piece', 'finger', 'head', 'orig_co')]:
        ob.data.attributes.remove(ob.data.attributes[at])
    mat = bpy.data.materials.new('Neutral'); mat.use_nodes = True
    ob.data.materials.clear(); ob.data.materials.append(mat)
    for o in bpy.data.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                              export_animations=False, export_skins=False, export_morph=False, export_attributes=False)
    print('UPLOAD', which, out, len(ob.data.polygons), 'faces')
    bpy.data.objects.remove(ob, do_unlink=True)
(P/'texturing').mkdir(exist_ok=True)
export('body',str(P/'texturing/ert_body_upload.glb'),'UVMap')
export('head',str(P/'texturing/ert_head_upload.glb'),'HeadUV')
print('HEAD FACES',int(head.sum()),'BODY FACES',len(head))
