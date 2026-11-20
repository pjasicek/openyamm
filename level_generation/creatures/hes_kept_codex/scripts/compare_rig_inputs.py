"""Compare actual uploads and ingest the female Meshy estimate without altering downloaded sources."""
import bpy,sys,os,json,hashlib,struct,math
from pathlib import Path
import numpy as np
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1]
report={}
for sex in 'mf':
 path=P/'work'/f'kept_{sex}_clean_v1.glb'
 raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n])
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30
 bpy.ops.import_scene.gltf(filepath=str(path))
 meshes=[o for o in bpy.data.objects if o.type=='MESH'];assert len(meshes)==1
 body=meshes[0];co=np.array([body.matrix_world@v.co for v in body.data.vertices])
 rings=json.loads((P/'work'/f'kept_{sex}_ring_joints.json').read_text())['joints']
 # Upper-arm shell centre at the same proportional height; wrists from the narrow surface rings.
 angles={}
 for sd,sg in [('L',1),('R',-1)]:
  sh=co[(co[:,2]>1.27)&(co[:,2]<1.33)&(co[:,0]*sg>.15)&(co[:,0]*sg<.25)].mean(0)
  wr=np.array(rings[sd+'_Hand']);d=wr-sh
  angles[sd]={'shoulder_surface_seed':sh.tolist(),'wrist':wr.tolist(),'arm_from_vertical_deg':float(np.degrees(np.arctan2(abs(d[0]),-d[2])))}
 feet=co[co[:,2]<.025]
 report[sex]=dict(file=str(path.relative_to(P)),sha256=hashlib.sha256(raw).hexdigest(),
  mesh_count=len(g['meshes']),mesh_nodes=len([n for n in g['nodes'] if 'mesh'in n]),
  primitives=len(g['meshes'][0]['primitives']),materials=len(g['materials']),
  height_m=float(np.ptp(co[:,2])),soles_z=float(co[:,2].min()),
  bounds_blender=[co.min(0).tolist(),co.max(0).tolist()],foot_bottom_center=((feet.min(0)+feet.max(0))/2).tolist(),
  gltf_node=g['nodes'][0],facing='glTF +Z / Blender -Y, visually verified',up='glTF +Y / Blender +Z',
  height_meters_request=1.7,arms=angles)
 if sex=='f': original=co.copy()
rigpath=P/'meshy/kept_f_joints_v1/result_rigged_character_glb_url.glb'
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
(P/'work/kept_f_meshy_joints.json').write_text(json.dumps(out,indent=2)+'\n')
report['female_return']=out
(P/'review/geometry/rig_input_comparison.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
