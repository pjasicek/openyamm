"""Measure the posed maul head, wrists, knees and forward reach at every 60 Hz sample."""
import bpy,sys,os,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
src=P/'work'/(args[0] if args else 'forge_final_clearance.blend');impact=1.75
bpy.ops.wm.open_mainfile(filepath=str(src));r=bpy.data.objects['Rig'];sc=bpy.context.scene;a=bpy.data.actions['Forge_Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
maul=bpy.data.objects['Thunder_Maul'];inv=r.data.bones['Thunder_Maul'].matrix_local.inverted();local=np.array([list(inv@(maul.matrix_world@v.co)) for v in maul.data.vertices]);head=local[local[:,1]>.82];centre=Vector((head.min(0)+head.max(0))/2)
assert len(head)>100 and .95<centre.y<1.1,(len(head),list(centre))
rows=[];floor=999;body=bpy.data.objects['Body'];worst=None
for f in np.arange(a.frame_range[0],a.frame_range[1]+.001,.5):
 sc.frame_set(int(f),subframe=float(f%1));m=armik.W(r,'Thunder_Maul');v=head@np.array(m.to_3x3()).T+np.array(m.translation);c=m@centre;pel=armik.W(r,'B_Pelvis');forward=(pel.to_3x3()@r.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted()@Vector((0,-1,0)));forward.z=0;forward.normalize()
 row={'frame':float(f),'time':float(f/30),'head_centre':list(c),'head_low':float(v[:,2].min()),'wrists_z':[armik.W(r,f'B_{s}_Hand').translation.z for s in 'LR'],'knees_z':[armik.W(r,f'B_{s}_Calf').translation.z for s in 'LR'],'front_of_pelvis_m':(c-pel.translation).dot(forward)};rows.append(row)
 e=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();z=np.array([(body.matrix_world@v.co).z for v in me.vertices]);i=int(z.argmin())
 if z[i]<floor:floor=float(z[i]);worst={'frame':float(f),'vertex':i,'z':floor,'groups':[(body.vertex_groups[g.group].name,g.weight) for g in body.data.vertices[i].groups]}
 e.to_mesh_clear()
hit=min(rows,key=lambda x:abs(x['time']-impact));lowest=min(rows,key=lambda x:x['head_low']);centre_low=min(rows,key=lambda x:x['head_centre'][2]);checks={'below_both_wrists':hit['head_centre'][2]<min(hit['wrists_z']),'below_both_knees':hit['head_centre'][2]<min(hit['knees_z']),'front_at_least_0_6m':hit['front_of_pelvis_m']>=.6,'head_lowest_within_two_frames':abs(lowest['frame']-hit['frame'])<=2,'head_centre_lowest_within_two_frames':abs(centre_low['frame']-hit['frame'])<=2,'head_near_floor':-.002<=hit['head_low']<=.035}
report={'passed':all(checks.values()),'checks':checks,'impact_s':impact,'impact':hit,'minimum_head_point':lowest,'minimum_head_centre':centre_low,'head_local_centre':list(centre),'body_floor_diagnostic':worst,'sample_hz':60,'master_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'samples':rows}
(P/'review/forge_slam_gate.json').write_text(json.dumps(report,indent=2)+'\n');print('SLAM_GATE',json.dumps({k:v for k,v in report.items() if k!='samples'}),flush=True)
assert report['passed'],checks
if src.name=='forge_final_clearance.blend':
 path=P/'review/gates_forge_concept.json';nine=json.loads(path.read_text());assert len(nine)==9
 values={'maul_head_height_m':hit['head_centre'][2],'maul_below_wrists_m':min(hit['wrists_z'])-hit['head_centre'][2],'maul_below_knees_m':min(hit['knees_z'])-hit['head_centre'][2],'maul_front_of_pelvis_m':hit['front_of_pelvis_m'],'maul_lowest_frame_offset':abs(lowest['frame']-hit['frame']),'maul_floor_clearance_m':hit['head_low']}
 nine['Forge_Attack'].update({k:{'value':float(v),'frame':hit['frame']} for k,v in values.items()});nine['Forge_Attack']['maul_slam_passed']=True;path.write_text(json.dumps(nine,indent=2)+'\n')
sys.stdout.flush();os._exit(0)
