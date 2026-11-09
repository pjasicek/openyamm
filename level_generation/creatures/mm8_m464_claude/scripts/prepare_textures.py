"""Preserve the fitted animated master; static full-body and separately unwrapped head uploads."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/fitted_garments.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
for o in bpy.context.scene.objects:o.select_set(o==body)
bpy.context.view_layer.objects.active=body
if not me.uv_layers:me.uv_layers.new(name='UVMap')
while len(me.uv_layers)>1:me.uv_layers.remove(me.uv_layers[-1])
head=[]
for f in me.polygons:
 z=sum(me.vertices[v].co.z for v in f.vertices)/len(f.vertices);head.append("Head" in me.materials[f.material_index].name)
for n in ['VampirePeasant_A','VampirePeasantHead_A']:
 mat=bpy.data.materials.get(n) or bpy.data.materials.new(n);mat.use_nodes=True
me.materials.clear();me.materials.append(bpy.data.materials['VampirePeasant_A']);me.materials.append(bpy.data.materials['VampirePeasantHead_A'])
for f,h in zip(me.polygons,head):f.material_index=int(h);f.select=h
assert sum(head)>100 and sum(head)<len(head)
(P/'work/head_uv_gate.json').write_text(json.dumps({'head_faces':sum(head),'policy':'Meshy unwrap for both sets: replacement hair and source face have overlapping source UVs'},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_uv.blend'))
def export(label,head_only):
 obj=body.copy();obj.data=me.copy();obj.parent=None;obj.modifiers.clear();obj.vertex_groups.clear();bpy.context.collection.objects.link(obj)
 if head_only:
  bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if not head[f.index]],context='FACES');bm.to_mesh(obj.data);bm.free()
 obj.data.materials.clear();mat=bpy.data.materials.new('Neutral_'+label);mat.use_nodes=True;obj.data.materials.append(mat)
 for f in obj.data.polygons:f.material_index=0
 for o in bpy.context.scene.objects:o.select_set(o==obj)
 bpy.context.view_layer.objects.active=obj;bpy.ops.export_scene.gltf(filepath=str(P/'work'/f'{label}_upload.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False,export_morph=False)
 bpy.data.objects.remove(obj,do_unlink=True)
export('body',False);export('head',True)
