"""Independent runtime bone audit with the shared evaluator and measured palm frames."""
import json,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parent/'claude_shared/gates'))
import run_gates as shared
palms=json.loads((P/'work/hand_rest_roll.json').read_text());cfg={'hands':{s:{'palm_axis':palms[s]['palm_local']}for s in 'LR'},'props':[],'cloth':[],'posture':{'*':{'pelvis_min_m':.9,'pelvis_max_m':1.15,'trunk_lean_deg':35},'Death':{'pelvis_min_m':.1,'pelvis_max_m':1.15,'trunk_lean_deg':95},'Dead':{'pelvis_min_m':.1,'pelvis_max_m':.4,'trunk_lean_deg':95}}}
sys.path.insert(0,str(P/'scripts'));from timing import phase
props=[{'name':'staff','node':'Staff','hands':[{'side':'R','intervals':{'Death':[[0,phase('Death',.12)]],'Dead':[]}},{'side':'L','clips':['Attack'],'grip_point':[0,0,.29],'intervals':{'Attack':[[phase('Attack',.4),phase('Attack',1.2)]]}}]}]
# The midpoint-based shared palm cone differs from the project's strict radial knuckle-normal gate.
cfg['thresholds']={'palm_grip_deg':65}
glb=shared.Glb(P/'export/mm6_jak1_runtime_lod0.glb');report=shared.Report(cfg)
for clip,animation,start,end in glb.clips():
 times=shared.sample_grid(start,end,48);shared.bone_gates(glb,glb.pose(animation,times),times,clip,cfg,report,props)
rows=list(report.rows.values());(P/'review/round2/shared_bone_audit.json').write_text(json.dumps({'sha256':glb.sha256,'runner_sha256':report.runner_sha256,'config':cfg,'rows':rows},indent=2))
failures=[r for r in rows if r['status']=='FAIL'];print('SHARED BONE FAILURES',[(r['clip'],r['gate'],r['region'],r['worst'],r['time_s'])for r in failures],flush=True)
# Prop-specific palm, grip and blade rules are covered by their project gates until final split exports exist.
checked={'rotation_step_deg','wrist_flexion_deg','wrist_roll_deg','upper_arm_roll_deg','forearm_roll_deg','elbow_hyperextension_deg','elbow_flexion_deg','elbow_plane_deg','roll_step_deg','angular_acceleration_deg_s2'}
assert not [r for r in failures if r['gate']in checked],failures
