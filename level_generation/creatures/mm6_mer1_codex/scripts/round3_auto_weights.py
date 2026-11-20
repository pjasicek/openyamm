import bpy,bmesh,sys,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common,reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round3/master_pretexture.blend'));C.reset();o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];s=bpy.context.scene;pv=[a.value for a in o.data.attributes['piece'].data]
a=o.data.attributes.new('source_index','INT','POINT');a.data.foreach_set('value',list(range(len(pv))))
shirt=o.copy();shirt.data=o.data.copy();s.collection.objects.link(shirt);shirt.modifiers.clear();shirt.parent=None;shirt.vertex_groups.clear();bm=bmesh.new();bm.from_mesh(shirt.data);part=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[part]!=1],context='VERTS');bm.to_mesh(shirt.data);bm.free()
heat=r.copy();heat.data=r.data.copy();s.collection.objects.link(heat);heat.animation_data_clear()
for b in heat.pose.bones:b.matrix_basis.identity()
bpy.ops.object.select_all(action='DESELECT');heat.select_set(True);bpy.context.view_layer.objects.active=heat;bpy.ops.object.mode_set(mode='EDIT')
chain={'B_Pelvis':'B_Spine','B_Spine':'B_Spine1','B_Spine1':'B_Spine2','B_Spine2':'B_Neck','B_Neck':'B_Head'}
for sd in 'LR':
 for a,b in [('Clavicle','UpperArm'),('UpperArm','Forearm'),('Forearm','Hand'),('Hand','Finger2')]:chain[f'B_{sd}_{a}']=f'B_{sd}_{b}'
for a,b in chain.items():heat.data.edit_bones[a].tail=heat.data.edit_bones[b].head
bpy.ops.object.mode_set(mode='OBJECT')
for b in heat.data.bones:b.use_deform=b.name in ['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck']+[f'B_{sd}_{n}'for sd in 'LR'for n in ['Clavicle','UpperArm','Forearm','Hand']]
bpy.ops.object.select_all(action='DESELECT');shirt.select_set(True);heat.select_set(True);bpy.context.view_layer.objects.active=heat;bpy.ops.object.parent_set(type='ARMATURE_AUTO')
for v in shirt.data.vertices:
 i=shirt.data.attributes['source_index'].data[v.index].value;w={shirt.vertex_groups[g.group].name:g.weight for g in v.groups};assert sum(w.values())>.5
 z=o.data.vertices[i].co.z;t=max(0,min(1,(1.07-z)/.075));t=t*t*(3-2*t);t*=max(0,min(1,(.34-abs(o.data.vertices[i].co.x))/.04))
 w={n:x*(1-t)for n,x in w.items()};w['B_Pelvis']=w.get('B_Pelvis',0)+t
 for g in list(o.data.vertices[i].groups):o.vertex_groups[g.group].remove([i])
 ws=sorted(w.items(),key=lambda x:-x[1])[:4];total=sum(x for n,x in ws)
 for n,x in ws:
  if x>1e-8:o.vertex_groups[n].add([i],x/total,'REPLACE')
bpy.data.objects.remove(heat,do_unlink=True)
bpy.data.objects.remove(shirt,do_unlink=True);o.data.attributes.remove(o.data.attributes['source_index']);C.reset();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round3/master_auto.blend'));common.workbench_clay(s,True)
for role,t in [('Standing',0),('Attack',.375),('Attack',.9167),('Death',1.3)]:
 C.activate(role,t);common.render_views(str(P/'review/round3'/f'auto_{role}_{t}'),1.15,1.2,views=('front','left','three_quarter'),resolution=(800,900))
