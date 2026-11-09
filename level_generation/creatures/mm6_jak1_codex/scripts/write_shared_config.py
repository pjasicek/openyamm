"""Declare the Jackalman's real prop, contact intervals and open wrap for the shared runtime audit."""
import json,sys,numpy as np
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as shared
sys.path.insert(0,str(P/'scripts'));from timing import phase
probe='--probe'in sys.argv;body='work/shared_probe_body.glb'if probe else'export/mm6_jak1.glb';staff='work/shared_probe_staff.glb'if probe else'export/mm6_jak1_staff.glb'
g=shared.Glb(P/body);pelvis=g.rest[g.names['B_Pelvis']];opening=(np.linalg.inv(pelvis)@np.array([0,0,.655,1]))[:3];axis=pelvis[:3,:3].T@np.array([0,0,-1])
cfg={'version':1,'hands':{s:{'palm_axis':json.loads((P/'work/hand_rest_roll.json').read_text())[s]['palm_local']}for s in 'LR'},'clips':{'attack':['Attack']},'posture':{'*':{'pelvis_min_m':.9,'pelvis_max_m':1.15,'trunk_lean_deg':35},'Death':{'pelvis_min_m':.1,'pelvis_max_m':1.15,'trunk_lean_deg':95},'Dead':{'pelvis_min_m':.1,'pelvis_max_m':.4,'trunk_lean_deg':95}},'props':[{'name':'staff','file':staff,'node':'Staff','kind':'melee','grip_point':[0,0,0],'tip':[.055,0,.76],'edge_axis':[1,0,0],'grip_surface':{'bounds':[[-.04,-.085,-.04],[.04,.085,.04]]},'hands':[{'side':'R','intervals':{'Death':[[0,phase('Death',.12)]],'Dead':[]}},{'side':'L','clips':['Attack'],'intervals':{'Attack':[[phase('Attack',.4),phase('Attack',1.2)]]},'grip_point':[0,0,.29],'surface':{'bounds':[[-.04,-.375,-.04],[.04,-.205,.04]]}}],'impacts':{'Attack':json.loads((P/'review/blow_gate.json').read_text())[0]['impact_s']}}],'cloth':[{'name':'open wrap skirt','surface':{'component_seeds':[[.1863179874,.135685862,.740712535]]},'samples':{'weights':['B_*_Thigh','B_*_Calf','B_*_Foot','B_*_Toe*','B_*_Hand','B_*_Finger*'],'weight_min':.3},'containment':False,'opening':{'node':'B_Pelvis','point':opening.tolist(),'axis':axis.tolist()}}],'thresholds':{'blow_pointing_deg':60,'palm_grip_deg':65},'previous_counts':{'body':{'colour':[10105,5052,1816,600],'shadow':[10105,5052,1816,600]},'staff':{'colour':[2924,1462,526,526]}},'refine_hz':48}

# An overlapping, split wrap has no single enclosing volume or planar hem.
# The final_panel_gate.py audit tests its actual outward fabric panels on all LODs.
cfg['cloth']=[]
cfg['thresholds']['lod3_ratio']=.24  # Combined actor remains ~10%; preserve the thin staff silhouette.
# Use actual underside vertices, excluding the curved upper sole and sandal side walls.
pose=g.pose(next(a for n,a,lo,hi in g.clips() if n=='Standing'),np.array([0.]))[0];cfg['lod_regions']={};cfg['sole_band_m']=.1
for mesh in shared.load_meshes(g):
 points=mesh.posed(pose);regions={}
 for side in 'LR':
  weighted=mesh.weight([f'B_{side}_Foot',f'B_{side}_Toe*'])>.5;low=points[weighted,2].min();ids=np.flatnonzero(weighted&(points[:,2]<=low+.004))
  assert len(ids)>=3,(mesh.label,side,len(ids));regions['foot_'+side]={'vertices':ids.tolist()}
 cfg['lod_regions'][mesh.label.split('/')[-1]]=regions

cfg['clip_thresholds']={name:{'foot_yaw_deg':36}for name in ['Standing','Fidget']}
cfg['clip_thresholds']['Walking']={'foot_yaw_deg':12}
name='shared_probe.gates.json'if probe else'gates.json';(P/name).write_text(json.dumps(cfg,indent=2));print(name)
