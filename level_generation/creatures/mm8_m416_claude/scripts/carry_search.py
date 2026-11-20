from pathlib import Path
import sys,math,json
p=Path(__file__).resolve();src=p.parent/'author_pilot.py';exec(compile(src.read_text().split('frames_by={};')[0],str(src),'exec'))
base=raw['Standing'][0];apply(base);S=armik.W(rig,'B_R_UpperArm').translation.copy();results=[]
for pitch in [40,50,60,70,80]:
 for yaw in [-30,0,30]:
  for roll in [-30,0,30]:
   B=Matrix.Rotation(math.radians(yaw),4,'Z')@Matrix.Rotation(math.radians(roll),4,'Y')@B0@Matrix.Rotation(math.radians(pitch),4,'X');B.translation=S+Vector((-.18,-.25,-.085));H=B@rels['R'];best=None
   for phi in range(-180,181,15):
    apply(base);u=(H.translation-S).normalized();pole=S+Quaternion(u,math.radians(phi))@Vector((-.8,0,-.5));reach=armik.solve(rig,'R',H.translation,pole=pole,hand_rot=H.to_3x3().normalized());sw,tw=armik.wrist_cost(rig,'R',H.to_3x3().normalized());elbow=armik.W(rig,'B_R_Forearm').translation;clear=max(0,elbow.x-S.x+.07)*1000;score=sw+.025*sw*sw+.3*abs(tw)+clear+abs(phi)*.02
    if best is None or score<best[0]:best=(score,sw,tw,phi)
   results.append({'pitch':pitch,'yaw':yaw,'roll':roll,'best':best,'score':best[0]+.2*abs(pitch-70)+.2*abs(yaw)+.2*abs(roll)})
results.sort(key=lambda x:x['score']);(P/'work/carry_search.json').write_text(json.dumps(results,indent=2));print('CARRY',results[:12],flush=True)
