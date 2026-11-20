import bpy,sys,runpy,json,math,itertools
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_carrier_poles.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];ax=bpy.data.objects['AxeMesh'];faces=[tuple(f.vertices) for f in b.data.polygons];af=[tuple(f.vertices) for f in ax.data.polygons];hands={g.index for g in b.vertex_groups if 'Hand' in g.name or 'Finger' in g.name};hw=[sum(g.weight for g in v.groups if g.group in hands) for v in b.data.vertices];fl=[f for f in faces if all(hw[i]<.2 for i in f)]
def co(obj):
 e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();xyz=[v.co.copy() for v in m.vertices];e.to_mesh_clear();return xyz
report={}
for role,f in [('Attack',120),('Attack',145),('Attack',155),('Cast',195),('Cast',295)]:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(f);xyz=co(b);av=co(ax);pairs=BVHTree.FromPolygons(av,af).overlap(BVHTree.FromPolygons(xyz,fl));report[role+str(f)]={'axe_crossings':len(pairs),'body_faces':[fl[j] for i,j in pairs[:8]]}
 if role=='Attack' and f==145:
  common.workbench_clay(bpy.context.scene,textured=True);common.render_views(str(P/'review/round1/carrier_test'),1,3.2,views=['front','left','three_quarter'],resolution=(640,640))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_lod0.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);corners=[]
for g in b.vertex_groups:
 if g.name not in r.pose.bones:continue
 pts=np.array([v.co[:] for v in b.data.vertices if any(x.group==g.index and x.weight>0 for x in v.groups)])
 if len(pts)==0:continue
 lo=pts.min(0);hi=pts.max(0);M=r.pose.bones[g.name].matrix@r.data.bones[g.name].matrix_local.inverted()
 corners.extend([M@Vector(x) for x in itertools.product(*zip(lo,hi))])
pts=np.array(corners);lo=pts.min(0);hi=pts.max(0);diam=float(np.linalg.norm(hi-lo));report['lod_calibration']={'bounds_min':lo.tolist(),'bounds_max':hi.tolist(),'bounds_diagonal_m':diam,'engine':'ModelRenderer uses cullingBounds; ModelLod.h uses AABB diagonal, not actor height.','actor_height_at_88_px':1.852535/diam*88};(P/'review/round1/probe_final.json').write_text(json.dumps(report,indent=2));print('FINAL PROBE',report,flush=True)
