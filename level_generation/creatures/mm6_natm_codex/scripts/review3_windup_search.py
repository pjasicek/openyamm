"""Fit a raised native wind-up with the same positive wrist roll as the forward thrust."""
from pathlib import Path
P=Path(__file__).resolve().parents[1]
s=(P/'scripts/review3_collision_search.py').read_text().split('results=[]')[0].replace('34/48','21/48').replace("axis=Vector((0,-1,0))","axis=Vector((.5,0,.8660254))")
s=s.replace("if sw<=65 and abs(tw)<=80", "if sw<=65 and (30<=tw<=80 if sd=='R'else abs(tw)<=80)")
exec(compile(s,str(P/'scripts/review3_collision_search.py'),'exec'))
L=(0,dict(Ra=r.pose.bones['B_L_UpperArm'].matrix.to_3x3(),Rf=r.pose.bones['B_L_Forearm'].matrix.to_3x3(),Rh=r.pose.bones['B_L_Hand'].matrix.to_3x3(),S=r.pose.bones['B_L_UpperArm'].head.copy(),E=r.pose.bones['B_L_Forearm'].head.copy(),W=r.pose.bones['B_L_Hand'].head.copy()),{})
out=[]
for x in [-.3,-.4,-.5,-.6]:
 for y in [-.20,-.10,0,.10,.20]:
  for z in [1.35,1.45,1.55,1.65]:
   G=Vector((x,y,z))
   for rr in solutions('R',G):
    c=contacts(rr,L);score=rr[0]+max(c.values())*1000+(G-Vector((-.4,.05,1.5))).length*100
    out.append((score,G.copy(),rr,c))
 print('WINDUP_SEARCH',x,len(out),flush=True)
out.sort(key=lambda x:x[0]);result=[]
for score,G,rr,c in out[:20]:
 sides['R'].apply(rr[1]);result.append({'score':score,'grip':list(G),'metrics':rr[2],'contacts':c,'bones':{f'B_R_{n}':list(r.pose.bones[f'B_R_{n}'].rotation_quaternion)for n in ['UpperArm','Forearm','Hand']}})
(P/'work/round3_windups.json').write_text(json.dumps(result,indent=2));print('BEST',result[:1],flush=True)
