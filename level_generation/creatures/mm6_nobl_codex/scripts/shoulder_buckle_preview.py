import bpy,numpy as np,sys
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v13.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data;sc=bpy.context.scene
pv=np.zeros(len(me.vertices),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
common.workbench_clay(sc,False);sc.display.shading.show_cavity=False;me.materials.clear()
for n,c in [('cloth',(.35,.6,.2,1)),('body',(.8,.08,.1,1)),('other',(.35,.35,.35,1))]:
 m=bpy.data.materials.new(n);m.diffuse_color=c;me.materials.append(m)
for f in me.polygons:f.material_index=0 if pv[f.vertices[0]]==0 else 1 if pv[f.vertices[0]]==1 else 2
for n,f in [('Walking',6),('Running',6),('Attack',15),('Hit',8),('Death',24),('Death',55)]:
 a=bpy.data.actions[n];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(f)
 if n!='Death':common.render_views(str(p/f'review/shoulder_buckle_20261011/trial_{n}_{f}'),1.31,.72,views=('front','back'),resolution=(650,650))
 else:
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();ids=np.flatnonzero((pv==0)&(np.array([v.co.z for v in me.vertices])>1.28));c=sum((em.vertices[int(i)].co for i in ids),Vector())/len(ids);ev.to_mesh_clear()
  cam=common.ortho_camera('cape',c+Vector((0,0,3)),(0,0,0),.85);sc.camera=cam;cam.rotation_quaternion=Vector((0,0,-1)).to_track_quat('-Z','Y');cam.rotation_mode='QUATERNION';sc.render.filepath=str(p/f'review/shoulder_buckle_20261011/trial_{n}_{f}.png');bpy.ops.render.render(write_still=True)
