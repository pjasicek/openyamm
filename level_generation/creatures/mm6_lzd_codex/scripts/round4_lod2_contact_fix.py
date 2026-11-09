import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));from rebake_render import render
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round4/contour2.blend'));r=bpy.data.objects['Rig'];ob=bpy.data.objects['Body'];me=ob.data;pv=np.array([x.value for x in me.attributes['piece'].data]);coords=np.array([tuple(v.co)for v in me.vertices]);changes=[]
for row in json.loads((P/'review/round4/lod2_contacts.json').read_text()):
 ids=[int(np.linalg.norm(coords-q,axis=1).argmin())for q in row['rest_surface_points']];assert max(np.linalg.norm(coords[i]-q)for i,q in zip(ids,row['rest_surface_points']))<1e-5
 assert len(set(pv[ids]))==1;part=pv[ids[0]];isbow=row['gate']=='prop_body_penetration_mm';clip,t,depth=('Death',1.0833333333333333,.0045)if isbow else('Walking',1/6,.002)
 a=bpy.data.actions[clip];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];f=t*30;bpy.context.scene.frame_set(int(f),subframe=f%1);matrices={g.index:r.pose.bones[g.name].matrix@r.data.bones[g.name].matrix_local.inverted()for g in ob.vertex_groups if g.name in r.pose.bones};delta=-Vector(row['normal'])*depth
 for v in me.vertices:
  if pv[v.index]!=part:continue
  distance=min((v.co-Vector(q)).length for q in row['rest_surface_points']);w=max(0,1-distance/.025)
  if not w:continue
  m=Matrix([[0]*4 for _ in range(4)])
  for g in v.groups:
   if g.group in matrices:m+=matrices[g.group]*g.weight
  v.co+=m.to_3x3().inverted()@(delta*w)
 changes.append({'gate':row['gate'],'piece':int(part),'displacement_m':depth,'vertices':ids})
r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();path=P/'work/round4/lod2_contact_final.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));(P/'review/round4/lod2_contact_fix.json').write_text(json.dumps(changes,indent=2));render(path,'round4_contact_final',2,parts=('actor',),palette=('round4_shared','lzd_a'),samples=32,camera_path=P/'review/round4/camera.json')
