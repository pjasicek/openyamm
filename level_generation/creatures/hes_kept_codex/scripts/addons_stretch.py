"""Dense first deformation probe; records failures rather than claiming final animation gates."""
import bpy,sys,os,json,math,hashlib
BODY_KIND = os.environ['KEPT_BODY']
assert BODY_KIND in ('male', 'female')
BODY_ID = 'm' if BODY_KIND == 'male' else 'f'
BODY_VERSION = 'v2' if BODY_ID == 'm' else 'v1'
from pathlib import Path
import numpy as np
from mathutils import Matrix,Quaternion
sys.path.insert(0,str(Path(__file__).parent));import kept_review_common as common
P=Path(__file__).resolve().parents[1]
source=Path(sys.argv[sys.argv.index('--')+1]).resolve();bpy.ops.wm.open_mainfile(filepath=str(source))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Kept'];me=body.data;scene=bpy.context.scene
names={g.index:g.name for g in body.vertex_groups};rest=np.array([v.co[:] for v in me.vertices])
E=np.array([e.vertices[:] for e in me.edges]);length=np.linalg.norm(rest[E[:,0]]-rest[E[:,1]],axis=1)
weights=np.zeros((len(rest),len(names)))
for v in me.vertices:
 for g in v.groups:weights[v.index,g.group]=g.weight
sums=weights.sum(1);assert sums.min()>.99 and sums.max()<1.01
masks={}
for sd in 'LR':
 hand=[i for i,n in names.items() if n.startswith('B_'+sd+'_') and ('Hand' in n or 'Finger' in n)]
 arm=[i for i,n in names.items() if n in [f'B_{sd}_{b}' for b in ('UpperArm','UpperArmTwist','Forearm','ForearmTwist','Hand')]]
 for what,groups in [('hand',hand),('arm',arm)]:
  w=weights[:,groups].sum(1);masks[sd+'_'+what]=(w[E[:,0]]>.3)&(w[E[:,1]]>.3)
report={'source':str(source.relative_to(P)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'bones':len(rig.data.bones),'weight_sum_range':[float(sums.min()),float(sums.max())],'max_influences':int((weights>1e-4).sum(1).max()),'clips':{},'scope':'Dense arm/hand edge stretch; additional contacts, feet, joint-frame and visual gates recorded separately'}
def posed():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
 co=np.array([v.co[:] for v in mesh.vertices]);ev.to_mesh_clear();return co
for action_name in sorted(a.name for a in bpy.data.actions if a.name.startswith('Kept_') and a.name not in ('Kept_ClubR2','Kept_ClubSword1')):
 action=bpy.data.actions[action_name];rig.animation_data.action=action
 if action.slots:rig.animation_data.action_slot=action.slots[0]
 start,end=action.frame_range;row={'duration_seconds':float((end-start)/30),'frames_sampled':0,'regions':{k:{'max':0,'p99':0} for k in masks}}
 for frame in np.arange(start,end+.25,.5):
  scene.frame_set(int(frame),subframe=float(frame%1));co=posed();assert np.isfinite(co).all()
  ratios=np.linalg.norm(co[E[:,0]]-co[E[:,1]],axis=1)/np.maximum(length,1e-6)
  for key,mask in masks.items():
   values=ratios[mask];r=row['regions'][key]
   if values.max()>r['max']:
    worst=np.where(mask)[0][np.argmax(values)]
    r.update(max=float(values.max()),frame=float(frame),edge=E[worst].tolist(),edge_vertices=[{'position':rest[v].tolist(),'weights':{names[i]:float(w) for i,w in enumerate(weights[v]) if w>.001}} for v in E[worst]])
   r['p99']=max(r['p99'],float(np.percentile(values,99)))
  row['frames_sampled']+=1
 row['arm_p99_pass']=all(v['p99']<=2 for k,v in row['regions'].items() if k.endswith('arm'))
 row['hand_max_pass']=all(v['max']<=4.5 for k,v in row['regions'].items() if k.endswith('hand'))
 report['clips'][action_name]=row
if 'probe' in sys.argv:
 (P/'review/addons_v2/attack_stretch.json').write_text(json.dumps(report,indent=2)+'\n')
 print('RESULT',[(k,[(n,round(v['max'],3),round(v['p99'],3)) for n,v in r['regions'].items()])for k,r in report['clips'].items()],flush=True)
 assert all(r['arm_p99_pass'] and r['hand_max_pass'] for r in report['clips'].values())
 print('STRETCH_PASS',BODY_KIND,len(report['clips']),flush=True);sys.stdout.flush();sys.stderr.flush();os._exit(0)
# CPU clay review, retaining the authoring file untouched.
mat=bpy.data.materials.new('PilotClay');mat.diffuse_color=(.62,.65,.68,1);me.materials.clear();me.materials.append(mat)
for poly in me.polygons:poly.material_index=0
common.workbench_clay(scene)
for action_name,frame in [('Kept_Standing',0),('Kept_Attack',10)]:
 action=bpy.data.actions[action_name];rig.animation_data.action=action
 if action.slots:rig.animation_data.action_slot=action.slots[0]
 scene.frame_set(frame)
 common.render_views(str(P/f'review/{BODY_KIND}'/action_name),.85,2.05,views=('front','left','three_quarter'),resolution=(512,768))
report['rest_frame_error_degrees']=max(math.degrees(rig.data.bones[n].matrix_local.to_quaternion().rotation_difference((Quaternion(v['q']).to_matrix()@Matrix(v['R_src'])).to_quaternion()).angle) for n,v in json.loads(scene['rig_offsets']).items())
assert report['rest_frame_error_degrees']<.1
(P/f'review/{BODY_KIND}/pilot_check.json').write_text(json.dumps(report,indent=2)+'\n')
print('PILOT',json.dumps(report),flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
