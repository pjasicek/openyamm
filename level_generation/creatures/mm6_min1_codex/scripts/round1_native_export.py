import bpy,json,itertools,runpy
import numpy as np
from mathutils import Vector
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/production_master.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);corners=[]
for g in b.vertex_groups:
 if g.name not in r.pose.bones:continue
 pts=np.array([v.co[:] for v in b.data.vertices if any(x.group==g.index and x.weight>0 for x in v.groups)])
 if not len(pts):continue
 lo=pts.min(0);hi=pts.max(0);m=r.pose.bones[g.name].matrix@r.data.bones[g.name].matrix_local.inverted();corners.extend([m@Vector(x) for x in itertools.product(*zip(lo,hi))])
pts=np.array(corners);lo=pts.min(0);hi=pts.max(0);d=float(np.linalg.norm(hi-lo));report={'bounds_min':lo.tolist(),'bounds_max':hi.tolist(),'bounds_diagonal_m':d,'tested_diagonal_m':2.689537525177002,'switch_pixels':[550,220,88],'source':'ModelAnimation modelPoseBounds; ModelLod AABB diagonal'};(P/'review/round1/lod_calibration.json').write_text(json.dumps(report,indent=2));print('FINAL CALIBRATION',report,flush=True)
runpy.run_path(str(P/'scripts/round1_final_native.py'))
