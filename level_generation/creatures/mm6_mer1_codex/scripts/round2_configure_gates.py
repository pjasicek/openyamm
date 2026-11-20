"""Record the merchant's existing garment and attachment intent for the shared gate runner."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as G
body=G.Glb(P/'export/mm6_mer1.glb');meshes=G.load_meshes(body);selection=json.loads((P/'review/reduction/selection.json').read_text());lods={}
for level,entry in enumerate(selection['body']):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/reduction/selected_lod{level}.blend'));o=bpy.data.objects['Body'];co=np.array([tuple(v.co)for v in o.data.vertices]);piece=np.array([v.value for v in o.data.attributes['piece'].data]);tree=KDTree(len(co))
 for i,v in enumerate(co):tree.insert(v,i)
 tree.balance()
 for mesh in [m for m in meshes if m.label.endswith(str(level))]:
  nearest=[tree.find(v)for v in mesh.rest];assert max(x[2]for x in nearest)<2e-5;part=piece[[x[1]for x in nearest]]
  ids=lambda mask:{'vertices':np.where(mask)[0].tolist()}
  lods[mesh.label.split('/')[-1]]={'head':ids((part==0)&(mesh.rest[:,2]>1.555)),'head_obstacles':ids(np.isin(part,[1,8,9])),'skirt':ids(part==2),'boots':ids(np.isin(part,[6,7])&(mesh.rest[:,2]<.84)),'shirt':ids(part==1),'hand_L':ids(part==3),'hand_R':ids(part==4)}
palms=json.loads((P/'work/round2/palm_normals.json').read_text());trace=json.loads((P/'review/final_source_motion_trace.json').read_text());limits={k:{g:v['source']['groups'][g]['degrees_per_sample']for g in ['arms','hands']}for k,v in trace['clips'].items()if v['source']}
cloth=[{'name':'coat hem','surface':'skirt','samples':'boots','opening':{'axis':[0,0,-1]}}]
for side in 'LR':
 hand=body.rest[body.names[f'B_{side}_Hand']];wrist=hand[:3,3];finger=body.rest[body.names[f'B_{side}_Finger2'],:3,3];axis=G.unit(finger-wrist)
 cloth.append({'name':side+' sleeve cuff','surface':'shirt','samples':'hand_'+side,'containment':True,'opening':{'node':f'B_{side}_Hand','point':[0,0,0],'axis':(hand[:3,:3].T@axis).tolist()}})
club=G.Glb(P/'export/mm6_mer1_club.glb');cm=G.load_meshes(club)[0];print('CLUB BOUNDS',cm.rest.min(0),cm.rest.max(0));print('CLUB NODE',body.rest[body.names['Club']])
config={'version':1,'forward':[0,-1,0],'floor_m':.001,'sole_band_m':.005,'refine_hz':48,'lod_regions':lods,'hands':{s:{'palm_axis':palms[s]}for s in 'LR'},'cloth':cloth,'props':[{'name':'club','file':'export/mm6_mer1_club.glb','node':'Club','kind':'other','grip_point':[0,0,0],'grip_surface':{'bounds':[[-.06,-.06,-.06],[.06,.06,.06]]},'hands':[{'side':'R','clips':['Attack'],'intervals':{'Attack':[[.21,1.55]]}}],'impacts':{'Attack':.8125}}],'source_rotation_limits':limits,'thresholds':{'palm_thigh_deg':45,'lod3_ratio':.18,'walking_knee_min_deg':39,'walking_knee_max_deg':61},'posture':{'*':{'pelvis_min_m':.65,'pelvis_max_m':1.1,'trunk_lean_deg':40},'Standing':{'pelvis_min_m':.8,'pelvis_max_m':1.1,'trunk_lean_deg':5},'Fidget':{'pelvis_min_m':.8,'pelvis_max_m':1.1,'trunk_lean_deg':5},'Death':{'pelvis_min_m':.05,'pelvis_max_m':1.1,'trunk_lean_deg':180},'Dead':{'pelvis_min_m':.05,'pelvis_max_m':.4,'trunk_lean_deg':180}}}
config['clip_thresholds']={k:{'angular_acceleration_deg_s2':max(g['acceleration_deg_s2']for g in v['source']['groups'].values())+10*48**2}for k,v in trace['clips'].items()if v['source']}
# Include cloth articulation in the runner's existing helper rotation-step checks.
config['bones']={f'ClothTwistMonitor_{i}_{k}':f'Cloak_{i}_{k}' for i in range(16) for k in range(4)}
config['previous_counts']={'body':{'colour':[9546,2420,2385,952]},'club':{'colour':[1122,290,252,200]}}
(P/'gates.json').write_text(json.dumps(config,indent=2))
