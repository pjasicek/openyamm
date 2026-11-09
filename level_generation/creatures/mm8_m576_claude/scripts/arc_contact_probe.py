import runpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];g=runpy.run_path(str(P.parent/'claude_shared/gates/run_gates.py'),run_name='probe');a=g['Glb'](P/'export/mm8_m576_lod0.glb');cfg=json.loads((P/'gates.json').read_text());r=g['Report'](cfg);m=g['load_meshes'](a)[0]
# The authoring export still carries the rigid prop in the body node: remove it from collision body targets.
m.vertices=m.vertices.copy();g['configure_mesh'](m,cfg,r);prop_mask=m.weight(['Trident'])>.9
for s in 'LR':m.surfaces[s]=g['Surface'](m,~m.regions['limb_'+s]&~prop_mask)
for name,c,start,end in a.clips():
 if name not in ('Attack','Hit','Running','Fidget'):continue
 worst={s:[0,0] for s in 'LR'};pw=[0,0]
 for t,p in zip(g['sample_grid'](start,end,48),a.pose(c,g['sample_grid'](start,end,48))):
  V=m.posed(p)
  for s in 'LR':
   d,i=g['penetration'](m.surfaces[s].build(V),V[m.contact_samples[s]])
   if d>worst[s][0]:worst[s]=[d,float(t)]
  surf=g['Surface'](m,~prop_mask&~m.regions['hand_L']);d,i=g['penetration'](surf.build(V),V[prop_mask])
  if d>pw[0]:pw=[d,float(t)]
 print('CONTACT',name,worst,'PROP',pw,flush=True)
