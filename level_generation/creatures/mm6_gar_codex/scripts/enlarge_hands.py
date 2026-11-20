"""Widen palm cross-sections and thicken finger shafts, retaining the fitted joint centres and UVs."""
import bpy,json,sys,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm6_bar1_claude/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_source_v2.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];scene=bpy.context.scene
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
co=np.array([v.co[:] for v in body.data.vertices]);delta=np.zeros_like(co)
uv=np.array([v.uv[:] for v in body.data.uv_layers.active.data]);chains=json.loads((P/'work/finger_chains.json').read_text())
weights=np.zeros((len(co),len(body.vertex_groups)))
for v in body.data.vertices:
 for g in v.groups:weights[v.index,g.group]=g.weight
names={g.name:g.index for g in body.vertex_groups}
def closest(points,chain):
 candidates=[]
 for a,b in zip(chain,chain[1:]):
  ab=b-a;t=np.clip((points-a)@ab/(ab@ab),0,1);candidates.append(a+t[:,None]*ab)
 candidates=np.array(candidates);which=np.argmin(np.linalg.norm(points-candidates,axis=2),axis=0)
 return candidates[which,np.arange(len(points))]
report={}
for side in ['L','R']:
 wrist=np.array(rig.data.bones[f'B_{side}_Hand'].head_local);fingers=np.array(chains[side]);knuckles=fingers[1:,0].mean(0)
 axis=knuckles-wrist;axis/=np.linalg.norm(axis)
 width=fingers[1,0]-fingers[4,0];width-=axis*(width@axis);width/=np.linalg.norm(width);depth=np.cross(axis,width)
 relative=co-wrist;radial=relative-np.outer(relative@axis,axis)
 palm_delta=.45*np.outer(radial@width,width)+.70*np.outer(radial@depth,depth)
 hand_weight=weights[:,names[f'B_{side}_Hand']]
 delta+=palm_delta*hand_weight[:,None]
 records=[]
 for f in range(5):
  prefix=f'B_{side}_Finger{f}';ids=[i for name,i in names.items() if name.startswith(prefix)]
  w=weights[:,ids].sum(1);centre=closest(co,fingers[f]);radius=co-centre
  factor=1.65 if side=='L' else 1.75
  delta+=(factor-1)*radius*w[:,None]
  mask=w>.9
  records.append({'finger':f,'shaft_scale':factor,'vertices':int(mask.sum()),'median_radius_before':float(np.median(np.linalg.norm(radius[mask],axis=1)))})
 report[side]={'palm_width_scale':1.45,'palm_depth_scale':1.70,'fingers':records}
# Diffuse the displacement across knuckles and the wrist instead of making stepped weight boundaries.
hand_ids=[i for n,i in names.items() if '_Hand' in n or '_Finger' in n]
strength=np.clip((weights[:,hand_ids].sum(1)-.1)/.7,0,1)
strength=strength*strength*(3-2*strength)
delta*=strength[:,None]
adj=[[] for _ in co]
for e in body.data.edges:
 a,b=e.vertices;adj[a].append(b);adj[b].append(a)
for _ in range(8):
 average=np.array([delta[ns].mean(0) if ns else delta[i] for i,ns in enumerate(adj)])
 delta=.45*delta+.55*average
 delta*=strength[:,None]
assert np.isfinite(delta).all() and np.linalg.norm(delta,axis=1).max()<.06
assert np.count_nonzero(np.linalg.norm(delta,axis=1)>1e-6)>200
common.workbench_clay(scene,textured=True)
scene.render.resolution_x=750;scene.render.resolution_y=750;scene.render.resolution_percentage=100
folder=P/'review/hands_v2';folder.mkdir(exist_ok=True)
def renders(label):
 for sd in ['L','R']:
  wrist=Vector(rig.data.bones[f'B_{sd}_Hand'].head_local);target=(wrist+Vector(chains[sd][2][1]))/2
  for view,direction in [('front',(0,-1,.3)),('palm',(1 if sd=='L' else -1,-.6,.35)),('side',(-1 if sd=='L' else 1,-.2,.3))]:
   loc=target+Vector(direction).normalized()*2;cam=common.ortho_camera('hand_camera',loc,(0,0,0),.46);cam.rotation_euler=(target-loc).to_track_quat('-Z','Y').to_euler();scene.camera=cam;scene.render.filepath=str(folder/f'{label}_{sd}_{view}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
renders('before')
for v,new in zip(body.data.vertices,co+delta):v.co=new
body.data.update();bpy.context.view_layer.update()
assert np.array_equal(uv,np.array([v.uv[:] for v in body.data.uv_layers.active.data]))
report['moved_vertices']=int(np.count_nonzero(np.linalg.norm(delta,axis=1)>1e-6));report['maximum_displacement_m']=float(np.linalg.norm(delta,axis=1).max());report['vertex_count']=len(co);report['uv_unchanged']=True
(P/'work/hand_volume_v2.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_hands_v2.blend'))
renders('after');print('HAND_VOLUME',report)
