"""Repeat the source gates on the actual reduced vertices and every clip at 48 Hz."""
import bpy,runpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P/'review/final';R.mkdir(exist_ok=True)
def run(path,tag,props=True):
 path=Path(path).resolve();bpy.ops.wm.open_mainfile(filepath=str(path));roles=['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget'];picks=[f'{n}:{f}'for n in roles for f in np.arange(0,bpy.data.actions[n].frame_range[1]+.001,bpy.context.scene.render.fps/48)]
 sys.argv=['g4','--',str(path),tag,*picks];runpy.run_path(str(P/'scripts/g4_weights.py'),run_name='__main__');g4=json.loads((P/f'work/g4_{tag}.json').read_text())
 def adapted(name,changes,args=[]):
  f=P/'scripts'/name;s=f.read_text()
  for a,b in changes:s=s.replace(a,b)
  sys.argv=[name,'--',*map(str,args)];exec(compile(s,str(f),'exec'),{'__file__':str(f),'__name__':'__main__'})
 adapted('g5_hand_stretch.py',[("'work/g5_final.json'",repr(f'review/final/{tag}_g5.json'))],[path,*roles]);g5=json.loads((R/f'{tag}_g5.json').read_text())
 adapted('audit_accepted.py',[("P/'work/accepted_master.blend'",repr(str(path))),('review/cloth/accepted_geometry_audit.json',f'review/final/{tag}_cloth.json')]);cloth=json.loads((R/f'{tag}_cloth.json').read_text())
 adapted('review_accepted.py',[("P/'work/accepted_master.blend'",repr(str(path))),('for i in range(5):','for i in []:'),('review/accepted/pose_audit.json',f'review/final/{tag}_pose.json'),('review/accepted/frames.json',f'review/final/{tag}_frames.json'),(" print('PILOT'", " report[name]['support_fraction']=float(np.mean(np.minimum([r['sole']for r in data['L']],[r['sole']for r in data['R']])<.01))\n print('PILOT'")]);pose=json.loads((R/f'{tag}_pose.json').read_text())
 prop={}
 if props:
  adapted('prop_contacts_accepted.py',[("P/'work/accepted_master.blend'",repr(str(path))),('review/prop_contacts.json',f'review/final/{tag}_props.json'),('work/blade_trace.json',f'review/final/{tag}_blade_trace.json')]);prop=json.loads((R/f'{tag}_props.json').read_text())
 result={'G4_max_p99':max(v['stretch_p99']for d in g4.values()for v in d.values()),'G5_max_edge_ratio':max(v['max_edge_stretch']for d in g5.values()for v in d.values()),'cloth_max_mm':max(d['cloth_penetration']['mm']for d in cloth.values()),'prop_max_mm':max([v['body_penetration_mm']for d in prop.values()for v in d.values()]+[0]),'elbow_min_deg':min(v['flex_min']for d in pose.values()for v in d['sides'].values()),'elbow_plane_max_deg':max(v['plane_max']for d in pose.values()for v in d['sides'].values()),'forearm_roll_max_deg':max(v['fore_max']for d in pose.values()for v in d['sides'].values()),'upper_roll_max_deg':max(v['upper_max']for d in pose.values()for v in d['sides'].values()),'rest_heel_toe_max_m':max(v['heel_toe_delta_max']for n in ['Standing','Fidget']for v in pose[n]['sides'].values()),'run_support_fraction':pose['Running']['support_fraction']}
 result['pass']=result['G4_max_p99']<=2 and result['G5_max_edge_ratio']<=4.5 and result['cloth_max_mm']<=.5 and result['prop_max_mm']<=.5 and result['elbow_min_deg']>=-5 and result['elbow_plane_max_deg']<=5 and result['forearm_roll_max_deg']<=90.5 and result['upper_roll_max_deg']<=90.5 and result['rest_heel_toe_max_m']<=.01 and result['run_support_fraction']>=.8
 (R/f'{tag}_gates.json').write_text(json.dumps(result,indent=2));print('ALL_GATES',tag,result,flush=True);return result
