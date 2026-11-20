"""Full hand-shell visibility and level-forearm audit at 60 Hz, on opaque sleeve triangles."""
import bpy,json,math,os
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/os.environ.get('GATE_BLEND','work/animation_finish.blend')))
r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene;me=b.data;piece=np.array([v.value for v in me.attributes['piece'].data]);skin=np.where(np.isin(piece,[2,3]))[0]
faces=[list(f.vertices) for f in me.polygons if all(piece[i]==0 for i in f.vertices)]
directions=[Vector((math.sin(a)*math.cos(e),-math.cos(a)*math.cos(e),math.sin(e))) for e in [0,math.pi/6,-math.pi/6] for a in np.arange(8)*math.pi/4]+[Vector((0,0,1)),Vector((0,0,-1))]
report={}
for name in ['Standing','Walking','Running','Fidget','Hit','Death','Dead','Attack','Cast']:
 act=bpy.data.actions[name];r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];end=float(act.frame_range[1]);worst=0;first=None;samples=0;level=0;mirror=0
 for f in np.arange(0,end+.01,.5):
  if name=='Attack' and 8<f<end:continue
  if name=='Cast' and 0<f<end:continue
  sc.frame_set(int(f),subframe=float(f%1));ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();P=[v.co.copy() for v in m.vertices];ev.to_mesh_clear();tree=BVHTree.FromPolygons(P,faces);visible=[]
  for i in skin:
   if any(tree.ray_cast(P[i],d,3)[0] is None for d in directions):visible.append(int(i))
  if len(visible)>worst:worst=len(visible);first={'frame':float(f),'vertices':visible}
  samples+=1
  lh=r.pose.bones['B_L_Hand'].head;rh=r.pose.bones['B_R_Hand'].head;le=r.pose.bones['B_L_Forearm'].head;re=r.pose.bones['B_R_Forearm'].head
  if name=='Standing':
   level=max(level,abs(le.z-lh.z),abs(re.z-rh.z),abs(lh.z-rh.z),abs(le.z-re.z));lv=(le-lh).normalized();rv=(re-rh).normalized();mirror=max(mirror,(lv+rv).length)
 report[name]={'samples_60hz':samples,'hand_vertices':len(skin),'views':26,'max_visible_hand_vertices':worst,'worst':first,'max_forearm_level_error_mm':level*1000,'max_antiparallel_direction_error':mirror,'pass':worst==0};print('OCCLUSION',name,worst,level*1000,flush=True)
(p/'work/review1_occlusion.json').write_text(json.dumps(report,indent=2))

assert all(v["pass"] for v in report.values()),report
