from pathlib import Path
p=Path(__file__).resolve();s=(p.parent/'author_pilot.py').read_text();exec(compile(s.split('frames_by={};')[0],str(p.parent/'author_pilot.py'),'exec'))
base=rels['L'].copy();results=[]
pose=raw['AimSource'][0].copy()

apply(pose);B=B0.copy();B.translation=armik.W(rig,'B_R_UpperArm').translation+Vector((-.05,-.34,.07));centre=Vector((0,.24,.06))
for delta in range(-180,181,15):
 rel=(Matrix.Rotation(math.radians(delta),4,'Y')@base);rel.translation=centre-rel.to_3x3()@Vector(G['L']['handle_centre_hand_local']);H=B@rel;best=None
 for phi in range(-180,181,10):
  apply(pose);S=armik.W(rig,'B_L_UpperArm').translation.copy();u=(H.translation-S).normalized();pole=Quaternion(u,math.radians(phi))@Vector((.8,0,-.5));reach=armik.solve(rig,'L',H.translation,pole=S+pole,hand_rot=H.to_3x3().normalized());sw,tw=armik.wrist_cost(rig,'L',H.to_3x3().normalized());E=armik.W(rig,'B_L_Forearm').translation
  c=sw+.025*sw*sw+.5*abs(tw)+1000*max(0,reach-.99)+500*max(0,E.z-H.translation.z)+500*max(0,H.translation.z-(B@centre).z)
  if best is None or c<best['cost']:best={'cost':c,'delta':delta,'phi':phi,'swing':sw,'twist':tw,'reach':reach,'wrist':list(H.translation),'elbow':list(E),'rel':[list(row) for row in rel]}
 results.append(best)
results.sort(key=lambda r:r['cost']);print('CALIBRATION',json.dumps(results[:8]));(P/'work/left_grip_calibration.json').write_text(json.dumps(results,indent=2))
