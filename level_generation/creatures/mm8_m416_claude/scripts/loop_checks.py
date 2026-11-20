"""Check delivered locomotion seams and the exact held corpse, including equipment."""
from pathlib import Path
import bpy,numpy as np,json
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm8_m416.blend'));r=bpy.data.objects['Rig'];o=bpy.data.objects['PirateCrossbowwoman'];sc=bpy.context.scene

def points(name,frame):
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(int(frame),subframe=float(frame%1));ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear();return co
out={}
for n in ['Standing','Walking','Running']:
 a=bpy.data.actions[n];error=float(np.linalg.norm(points(n,a.frame_range[0])-points(n,a.frame_range[1]),axis=1).max());out[n]={'maximum_loop_surface_error_m':error};assert error<.004,(n,error)
end=points('Death',bpy.data.actions['Death'].frame_range[1]);out['Death_to_Dead_m']=float(np.linalg.norm(end-points('Dead',0),axis=1).max());assert out['Death_to_Dead_m']<1e-5
(P/'review/loop_checks.json').write_text(json.dumps(out,indent=2));print('LOOPS',out)

