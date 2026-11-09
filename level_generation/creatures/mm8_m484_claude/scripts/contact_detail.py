"""Half-frame surface contacts on the closed skin, separate mail and rigid axe."""
import os
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import numpy as np
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/gated_master.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];ax=bpy.data.objects['AxeMesh'];sc=bpy.context.scene;me=b.data;rest=np.array([v.co[:] for v in me.vertices]);pv=np.array([v.value for v in me.attributes['piece'].data]);ng=[g.name for g in b.vertex_groups];W=np.zeros((len(rest),len(ng)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
faces=[tuple(f.vertices) for f in me.polygons];skin=[f for f in faces if all(pv[i] in [0,1] for i in f)];cloth=[f for f in faces if all(pv[i]==100 and rest[i,2]<.86 for i in f)]
part={}
for sd in 'RL':
 arm=W[:,[i for i,n in enumerate(ng) if n.startswith(f'B_{sd}_') and any(k in n for k in ['UpperArm','Forearm','Hand','Finger'])]].sum(1);hand=W[:,[i for i,n in enumerate(ng) if n.startswith(f'B_{sd}_') and any(k in n for k in ['Forearm','Hand','Finger'])]].sum(1)
 part[sd]={'faces':[f for f in skin if all(arm[i]<.15 for i in f)],'ids':np.where(hand>.7)[0],'handfaces':[f for f in skin if all(hand[i]>.7 for i in f)]}
def coords(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();a=np.array([tuple(o.matrix_world@v.co) for v in m.vertices]);ev.to_mesh_clear();return a
report=json.loads((P/'review/upperarm_contacts.json').read_text())['Attack'];act=bpy.data.actions['Attack'];r.animation_data.action=act;r.animation_data.action_slot=act.slots[0]
for label,hit in report.items():
 if not hit['depth_m']:continue
 f=hit['frame'];sc.frame_set(int(f),subframe=f%1);co=coords(b);fs=skin if label=='axe' else part[label[0]]['faces'];fi=fs[hit['face']];i=hit['vertex'];print('COLLISION',label,'frame',f,'depth',hit['depth_m'],'target',fi,'target posed',co[list(fi)].mean(0),'target weights',{ng[k]:round(float(W[list(fi),k].mean()),3) for k in range(len(ng)) if W[list(fi),k].mean()>.1})
 if label!='axe':print('QUERY',i,'posed',co[i],'weights',{ng[k]:round(float(W[i,k]),3) for k in range(len(ng)) if W[i,k]>.1})

print("REST",{i:rest[i].tolist() for i in [452,163,1192,370]});print("BONES",{n:list(r.data.bones[n].head_local) for n in ["B_R_UpperArm","B_R_Forearm","B_R_Hand"]})
