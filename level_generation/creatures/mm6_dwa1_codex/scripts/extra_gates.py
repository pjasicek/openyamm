import bpy,json,math,numpy as np,sys,runpy
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/export_reimport.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];axe=bpy.data.objects['Axe'];scene=bpy.context.scene;pv=np.array([a.value for a in body.data.attributes['piece'].data]);rest=[body.matrix_world@v.co for v in body.data.vertices];skirt=[tuple(f.vertices)for f in body.data.polygons if pv[f.vertices[0]]==2];skin=[v.index for v in body.data.vertices if pv[v.index]==5 and v.co.z>.45]
def pose_points(ob):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();p=[ob.matrix_world@v.co for v in m.vertices];ev.to_mesh_clear();return p
def skirt_side(co):
 tree=BVHTree.FromPolygons(co,skirt);out={}
 for i in skin:
  p=co[i];loc,n,fi,d=tree.find_nearest(p,.08)
  if loc is not None:out[i]=(bool((p-loc).dot(n)>.7071*d),float(d))
 return out
baseline=skirt_side(rest);report={};A=rig.data.bones['Axe'].matrix_local;Ai=A.inverted();av=[Ai@(axe.matrix_world@v.co)for v in axe.data.vertices];tip=max(av,key=lambda p:p.y);edge=Vector((1,0,0))
# Reconstruct the modelled bit's cutting-side vector from the known canonical input and the original rig frame.
with bpy.data.libraries.load(str(P/'work/textured_master.blend'),link=False)as(src,dst):dst.objects=['Rig']
ref=dst.objects[0];orig=ref.data.bones['B_R_Hand'].matrix_local@Matrix(json.loads((P/'work/axe_attachment.json').read_text())['hand_local_matrix']);tip=Ai@(orig@Vector((.405,0,-.175)));edge=(Ai.to_3x3()@(orig.to_3x3()@Vector((0,0,-1)))).normalized();axis=(Ai.to_3x3()@(orig.to_3x3()@Vector((1,0,0)))).normalized();bpy.data.objects.remove(ref);report['axe_reference']={'edge_local':list(edge),'axis_local':list(axis),'blade_point_local':list(tip)}
for name in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];rows=[];worst=[0,None,None];floors=[];prev=None
 for f in np.arange(0,float(a.frame_range[1])+1e-6,scene.render.fps/48):
  scene.frame_set(int(f),subframe=float(f-int(f)));co=pose_points(body);floors.append(min(v.z for v in co));M=rig.matrix_world@rig.pose.bones['Axe'].matrix;pt=M@tip;ed=(M.to_3x3()@edge).normalized();ax=(M.to_3x3()@axis).normalized()
  if prev:
   v=(pt-prev[0])*48;speed=v.length;flat=ax.cross(ed).normalized();lead=v.normalized().dot(ed)if speed>1e-9 else 0;share=abs(v.dot(ed))/max(math.hypot(v.dot(ed),v.dot(flat)),1e-9);rows.append({'seconds':(f+prev[1])/2/scene.render.fps,'speed':speed,'signed_lead':lead,'edge_share':share,'forward':-ax.y})
  prev=(pt,f)
  for i,(outside,d)in skirt_side(co).items():
   if outside and i in baseline and not baseline[i][0] and d>worst[0]:worst=[d,float(f/scene.render.fps),i]
 report[name]={'floor_min_max_m':[min(floors),max(floors)],'open_hem_nearest_face_diagnostic_not_penetration':worst}
 if name=='Attack':
  hit=max([r for r in rows if r['forward']>.5],key=lambda r:r['speed']);report[name]['blow']=hit;assert hit['signed_lead']>.4 and hit['edge_share']>.8,hit
 print('EXTRA',name,report[name],flush=True)
(P/'review/extra_exported_gates.json').write_text(json.dumps(report,indent=2))
runpy.run_path(str(P/'scripts/export_motion_metrics.py'),run_name='__main__')
