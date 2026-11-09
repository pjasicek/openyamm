"""Measure the off-hand palm surface around the fitted shaft contact patch."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_lod0.blend'));C.activate('Attack',34/48);r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];g=json.loads((P/'work/round3_left_grip.json').read_text());H=r.pose.bones['B_L_Hand'].matrix;inv=H.inverted();centre=Vector(g['handle_centre_hand_local']);axis=Vector(g['handle_axis_hand_local']);old=Vector((.009,.102,-.995));weight=np.array([sum(a.weight for a in v.groups if body.vertex_groups[a.group].name=='B_L_Hand')for v in body.data.vertices]);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles();rows=[]
for t in m.loop_triangles:
 if min(weight[list(t.vertices)])<.55:continue
 a,b,c=[inv@m.vertices[i].co for i in t.vertices];normal=(b-a).cross(c-a);area=normal.length*.5
 if area<1e-10:continue
 normal.normalize();mid=(a+b+c)/3;delta=mid-centre;rad=(delta-axis*delta.dot(axis)).length
 if normal.dot(old)<.5 or abs(delta.dot(axis))>.035 or rad>.055:continue
 rows.append({'normal':list(normal),'area':area,'radial':rad,'centre':list(mid)})
normal=np.average([row['normal']for row in rows],axis=0,weights=[row['area']/(.005+row['radial'])for row in rows]);normal/=np.linalg.norm(normal)
(P/'review/round3_palm_surface.json').write_text(json.dumps({'hand_local_normal':normal.tolist(),'triangles':rows,'method':'Area/distance weighted normals of hand-dominant palm triangles facing the shaft, within 35 mm along and 55 mm radially of the grip line.'},indent=2));print('PALM_SURFACE_NORMAL',normal.tolist(),len(rows),flush=True);ev.to_mesh_clear()
