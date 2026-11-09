import bpy,json,sys,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];report={}
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/final_lod{level}.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];shield=bpy.data.objects['LeafShield'];sc=bpy.context.scene;me=body.data;lab=np.array([v.value for v in me.attributes['finger'].data]);co=np.array([tuple(v.co)for v in me.vertices]);names=[g.name for g in body.vertex_groups];palm=np.array([v.index for v in me.vertices if co[v.index,0]>0 and sum(g.weight for g in v.groups if names[g.group]=='B_L_Hand')>.7]);digits={str(i):np.where((lab==i+1)&(co[:,0]>0))[0]for i in range(5)};M=rig.data.bones['LeafShield'].matrix_local.inverted();vc=[M@v.co for v in shield.data.vertices];faces=[tuple(f.vertices)for f in shield.data.polygons if all(abs(vc[i].x)<.09 and abs(vc[i].y-.045)<.022 and abs(vc[i].z-.26)<.021 for i in f.vertices)];assert len(faces)>0,(level,len(faces));tree=BVHTree.FromPolygons(vc,faces);palmset=set(palm);palmfaces=[tuple(f.vertices)for f in me.polygons if all(i in palmset for i in f.vertices)];assert palmfaces,level;probes=[tree.find_nearest(Vector((x,.045+.011*np.cos(a),.26+.011*np.sin(a))))[0]for x in np.linspace(-.06,.06,49)for a in np.arange(32)*np.pi/16];report[str(level)]={}
 for name in ['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']:
  a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];row={'palm_gap_max_mm':0,'digits_nearest_max_mm':{str(i):0 for i in range(5)}}
  for f in np.arange(0,a.frame_range[1]+.001,sc.render.fps/48):
   sc.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();pts=[v.co.copy()for v in mm.vertices];ev.to_mesh_clear();iv=rig.pose.bones['LeafShield'].matrix.inverted()
   for group,ids in [('palm',palm),*digits.items()]:
    value=min(tree.find_nearest(iv@pts[int(i)])[3]for i in ids)*1000
    if group=='palm':
     ptree=BVHTree.FromPolygons([iv@v for v in pts],palmfaces);value=min(value,min(ptree.find_nearest(q)[3]for q in probes)*1000);row['palm_gap_max_mm']=max(row['palm_gap_max_mm'],value)
    else:row['digits_nearest_max_mm'][group]=max(row['digits_nearest_max_mm'][group],value)
  report[str(level)][name]=row
 print('GRIP_FINAL',level,max(v['palm_gap_max_mm']for v in report[str(level)].values()),flush=True)
(P/'review/final/grip_contact.json').write_text(json.dumps(report,indent=2))
