"""Compare a skin-only heat bind at the already fitted joints with the coarse service weights."""
import bpy,bmesh,numpy as np,sys,runpy
from pathlib import Path
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_weighted_final.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix()
piece=np.array([x.value for x in body.data.attributes['piece'].data]);co=np.array([v.co[:] for v in body.data.vertices])
heat=body.copy();heat.data=body.data.copy();bpy.context.collection.objects.link(heat);heat.name='HeatSkin';heat.modifiers.clear();heat.vertex_groups.clear();heat.parent=None
bm=bmesh.new();bm.from_mesh(heat.data);attr=bm.verts.layers.int.new('source_vertex')
for v in bm.verts:v[attr]=v.index
bmesh.ops.delete(bm,geom=[v for v in bm.verts if piece[v.index] not in (0,7)],context='VERTS')
bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0);bm.to_mesh(heat.data);bm.free()
arm=bpy.data.armatures.new('HeatBones');ar=bpy.data.objects.new('HeatBones',arm);bpy.context.collection.objects.link(ar);bpy.context.view_layer.objects.active=ar;ar.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
names=[n for n in rig.data.bones.keys() if n.startswith('B_') and not any(x in n for x in ('Finger','Twist'))]
for n in names:
 src=rig.data.bones[n];b=arm.edit_bones.new(n);b.head=src.head_local
 children=[c for c in src.children if c.name in names]
 if 'Hand' in n:b.tail=rig.data.bones[n.replace('Hand','Finger2')].head_local
 elif children:b.tail=next((c for c in children if not any(x in c.name for x in ('Thigh','Clavicle'))),children[0]).head_local
 else:b.tail=b.head+Vector((0,0,.10))
 if src.parent and src.parent.name in names:b.parent=arm.edit_bones[src.parent.name]
bpy.ops.object.mode_set(mode='OBJECT')
for o in bpy.context.scene.objects:o.select_set(o in (heat,ar))
bpy.context.view_layer.objects.active=ar;bpy.ops.object.parent_set(type='ARMATURE_AUTO')
ids=[x.value for x in heat.data.attributes['source_vertex'].data];hn={g.index:g.name for g in heat.vertex_groups};dest={g.name:g for g in body.vertex_groups};changed=0
for v,original in zip(heat.data.vertices,ids):
 xyz=co[original]
 if piece[original]!=0 or xyz[2]<1.15 or xyz[2]>1.55:continue
 ws={hn[g.group]:g.weight for g in v.groups};total=sum(ws.values());assert total>.1,(original,total)
 for g in body.vertex_groups:g.remove([original])
 for n,w in ws.items():
  if w>1e-6:dest[n].add([original],w/total,'REPLACE')
 changed+=1
print('HEAT_BIND',changed,flush=True)
bpy.data.objects.remove(heat,do_unlink=True);bpy.data.objects.remove(ar,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_heat.blend'))
sys.argv=['g4_weights.py','--',str(p/'work/rig_heat.blend'),'heat','Standing:0','Attack:14','Attack:18','Hit:5','Death:28'];runpy.run_path(str(p/'scripts/g4_weights.py'),run_name='__main__')
