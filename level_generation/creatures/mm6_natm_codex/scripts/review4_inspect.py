import bpy,json,sys,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_lod0.blend'));r=bpy.data.objects['Rig'];out={}
names=[b.name for b in r.pose.bones if b.name.startswith(('Feather','Cloth'))]
for role in C.ROLES:
 C.reset();C.activate(role,0);out[role]={n:{'parent':r.data.bones[n].parent.name,'location':list(r.pose.bones[n].location),'scale':list(r.pose.bones[n].scale),'rotation':list(r.pose.bones[n].rotation_quaternion)}for n in names}
print('COSTUME',json.dumps(out),flush=True)
body=bpy.data.objects['Body'];pieces=np.array([x.value for x in body.data.attributes['piece'].data]);co=np.array([v.co[:]for v in body.data.vertices]);stats={str(i):{'count':int((pieces==i).sum()),'bounds':[co[pieces==i].min(0).tolist(),co[pieces==i].max(0).tolist()]}for i in np.unique(pieces)};print('PIECES',json.dumps(stats),flush=True)
(P/'review/round4_before_inspection.json').write_text(json.dumps({'costume':out,'pieces':stats},indent=2))
