"""Ingest the successful male retry as an independent joint reference; preserve downloads."""
import bpy, sys, os, json, hashlib
from pathlib import Path
import numpy as np
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/kept_m_clean_v2.blend'))
body=bpy.data.objects['Body'];original=np.array([body.matrix_world@v.co for v in body.data.vertices])
rigpath=P/'meshy/kept_m_joints_v2/result_rigged_character_glb_url.glb'
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(rigpath))
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH')
arm.animation_data_clear();arm.data.pose_position='REST'
co=np.array([body.matrix_world@v.co for v in body.data.vertices])
scale=float(np.ptp(original[:,2])/np.ptp(co[:,2]))
centre=lambda c:np.array([(c[:,0].min()+c[:,0].max())/2,(c[:,1].min()+c[:,1].max())/2,c[:,2].min()])
offset=centre(original)-centre(co)*scale
mapped=co*scale+offset
kd=KDTree(len(mapped))
for i,c in enumerate(mapped):kd.insert(c,i)
kd.balance();dist=np.array([kd.find(c)[2] for c in original])
assert dist.max()<1e-5,dist.max()
MAP={'Hips':'Pelvis','Spine02':'Spine','Spine01':'Spine1','Spine':'Spine2','neck':'Neck','Head':'Head'}
for side,sd in [('Left','L'),('Right','R')]:
 MAP.update({side+x:sd+'_'+y for x,y in [('Shoulder','Clavicle'),('Arm','UpperArm'),('ForeArm','Forearm'),('Hand','Hand'),('UpLeg','Thigh'),('Leg','Calf'),('Foot','Foot'),('ToeBase','Toe0')]})
joints={MAP[b.name]:(np.array(arm.matrix_world@b.head_local)*scale+offset).tolist() for b in arm.data.bones if b.name in MAP}
assert len(joints)==22
out=dict(source=str(rigpath.relative_to(P)),source_sha256=hashlib.sha256(rigpath.read_bytes()).hexdigest(),scale=scale,offset=offset.tolist(),joints=joints,all_bones=[b.name for b in arm.data.bones],geometry_match_max_m=float(dist.max()),status='independent_estimate_pending_composition')
(P/'work/kept_m_meshy_joints.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out),flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
