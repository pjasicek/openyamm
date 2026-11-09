"""Verify the installed-format weapon arc, event timing, hold and return to the accepted guard."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
import yaml
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/floor'));from glb_pose import Glb,Model
A=P/'work/before_strike_20261024';m=Model(Glb(P/'export/hes_forgemaster.glb'));item=Model(Glb(P/'export/hes_thunder_maul.glb'));v=np.vstack([x for x,_ in item.skinned_positions(item.world({}))]);v=v[v[:,1]>.82];centre=(v.min(0)+v.max(0))/2;v=np.column_stack([v,np.ones(len(v))]);nm={n.get('name'):i for i,n in enumerate(m.glb.json['nodes'])};rest=m.world({});fwdlocal=np.linalg.inv(rest[nm['B_Pelvis']][:3,:3])@np.array([0.,0.,1.])
bindings=yaml.safe_load((P/'integration/actors.yml').read_text());forge=next(x for x in bindings if x['descriptor']=='Forgemaster');events=forge['animation']['events'];impact=events['attack_melee']['impact'];assert impact==events['attack_ranged']['impact']==1.75;assert m.clip_times('Forge_Attack')[-1]==3.5
rows=[]
for t in np.arange(0,3.50001,1/60):
 w=m.world(m.sample('Forge_Attack',float(t)));M=w[nm['Thunder_Maul']];head=M@np.r_[centre,1];points=v@M.T;pel=w[nm['B_Pelvis']];forward=pel[:3,:3]@fwdlocal;forward[1]=0;forward/=np.linalg.norm(forward)
 rows.append({'time':float(t),'head_centre':head[:3].tolist(),'head_low_m':float(points[:,1].min()),'wrists_height':[float(w[nm[f'B_{s}_Hand']][1,3]) for s in 'LR'],'knees_height':[float(w[nm[f'B_{s}_Calf']][1,3]) for s in 'LR'],'front_of_pelvis_m':float((head[:3]-pel[:3,3])@forward)})
hit=min(rows,key=lambda x:abs(x['time']-impact));low=min(rows,key=lambda x:x['head_low_m']);assert hit['head_centre'][1]<min(hit['wrists_height']) and hit['head_centre'][1]<min(hit['knees_height']);assert hit['front_of_pelvis_m']>=.6 and abs(low['time']-impact)<=2/60;assert -.002<=hit['head_low_m']<=.035
held=[r for r in rows if impact<=r['time']<=2.0];hold_motion=max(np.linalg.norm(np.array(r['head_centre'])-hit['head_centre']) for r in held);assert hold_motion<.003
old=Model(Glb(A/'export/hes_forgemaster.glb'));on={n.get('name'):i for i,n in enumerate(old.glb.json['nodes'])};before=old.world(old.sample('Forge_Attack',2.5));after=m.world(m.sample('Forge_Attack',3.5));guard=[]
for n in nm:
 if not any(x in n for x in ('Hand','UpperArm','Forearm','Thunder_Maul')):continue
 r=after[nm[n]][:3,:3]@before[on[n]][:3,:3].T;angle=float(np.degrees(np.arccos(np.clip((np.trace(r)-1)/2,-1,1))));distance=float(np.linalg.norm(after[nm[n]][:3,3]-before[on[n]][:3,3]));assert angle<1 and distance<.001,(n,angle,distance);guard.append({'bone':n,'degrees':angle,'distance_m':distance})
hashfile=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();unchanged={}
def same_content(a,b):
 # Tier colours (2026-10-24) changed only material ramps/glow factors: meshes, indices and clips must still match.
 x,y=Glb(a),Glb(b);mx,my=x.json['meshes'],y.json['meshes'];assert len(mx)==len(my)
 for ma,mb in zip(mx,my):
  for pa,pb in zip(ma['primitives'],mb['primitives'],strict=True):
   assert pa['attributes'].keys()==pb['attributes'].keys()
   for k in pa['attributes']:assert np.array_equal(x.accessor(pa['attributes'][k]),y.accessor(pb['attributes'][k]))
   assert np.array_equal(x.accessor(pa['indices']),y.accessor(pb['indices']))
 for aa,ab in zip(x.json.get('animations',[]),y.json.get('animations',[]),strict=True):
  for sa,sb in zip(aa['samplers'],ab['samplers'],strict=True):
   for k in ('input','output'):assert np.array_equal(x.accessor(sa[k]),y.accessor(sb[k]))
 return True
for n in ('hes_lancer','hes_ion_lance','hes_ion_lance_twin','hes_lancer_graft','hes_thunder_maul'):
 h=hashfile(P/f'export/{n}.glb');assert h==hashfile(A/f'export/{n}.glb') or same_content(P/f'export/{n}.glb',A/f'export/{n}.glb'),n;unchanged[n]=h
report={'passed':True,'impact_s':impact,'duration_s':3.5,'impact':hit,'lowest':low,'sample_hz':60,'hold_s':.25,'hold_head_motion_m':float(hold_motion),'return_to_accepted_guard':guard,'unchanged_export_hashes':unchanged,'forgemaster_sha256':hashfile(P/'export/hes_forgemaster.glb')};(P/'review/forge_slam_runtime_gate.json').write_text(json.dumps(report,indent=2)+'\n');print('RUNTIME_SLAM_PASS',json.dumps(hit),'hold movement',hold_motion)
