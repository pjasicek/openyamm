"""Select the neutral carry from native-shaped candidates with actual arm and skin constraints."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]
s=(p/'scripts/motion_fit.py').read_text();exec(compile(s[:s.index('report={}')],str(p/'scripts/motion_fit.py'),'exec'))
PH=np.arange(-180,180,30);PS=np.arange(0,360,30)
dp=np.zeros((len(PH),len(PH)));ds=np.zeros((len(PS),len(PS)))
setact(bpy.data.actions['Standing']);sc.frame_set(0);snap={b.name:b.matrix_basis.copy() for b in rig.pose.bones};setact(None);restore(snap)
world={n:np.array(armik.W(rig,n)) for n in rig.pose.bones.keys()};clav={s:armik.W(rig,'B_'+s+'_Clavicle').to_3x3().normalized() for s in 'RL'}
mats={}
for side in 'RL':
 n='B_'+side+'_Clavicle';D=armik.W(rig,n)@rig.data.bones[n].matrix_local.inverted();mats[side]=[D@rig.data.bones['B_'+side+'_'+part].matrix_local for part in ('UpperArm','Forearm','Hand')]
rows=[]
for x in (-.10,0,.10):
 for y in (-.20,-.35):
  for z in (1.20,1.35,1.50):
   for lean in (.35,.60,.80):
    center=Vector((x,y,z));axis=Vector((lean,-.2,math.sqrt(1-lean*lean))).normalized();base={s:armik.hand_rot(A[s],axis,0) for s in 'RL'}
    fr={'snap':snap,'world':world,'clavicle':clav,'mat':mats,'center':center,'axis':axis,'base':base};stats={}
    for side in 'RL':
     phi,psi=fit_side(side,[fr])[0];R=Quaternion(axis,math.radians(psi)).to_matrix()@base[side];T=center-(axis*.15 if side=='L' else Vector())-R@C[side]
     F,_,reach,U,E,T=fitted(*mats[side],T,phi);names=['B_'+side+'_'+n for n in ('UpperArm','Forearm','Hand')]
     rel=(rig.data.bones[names[1]].matrix_local.to_3x3().inverted()@rig.data.bones[names[2]].matrix_local.to_3x3()).inverted();q=(rel@F.inverted()@R).to_quaternion();sw,tw=armik.split_swing_twist(q,Vector((0,1,0)));sw=math.degrees(min(sw.angle,2*math.pi-sw.angle))
     parts,edge,length=cost_data[side];posed=sum((v@world[n].T)[:,:3] for n,v in parts.items() if n not in names)
     for n,rot,loc in zip(names,(U,F,R),(mats[side][0].translation,E,T)):
      if n not in parts:continue
      M=rot.to_4x4();M.translation=loc;posed+=(parts[n]@np.array(M).T)[:,:3]
     ratio=np.linalg.norm(posed[edge[:,0]]-posed[edge[:,1]],axis=1)/np.maximum(length,1e-6)
     stats[side]={'swing':sw,'twist':math.degrees(tw),'reach':reach,'p99':float(np.quantile(ratio,.99))}
    score=sum(v['swing']+200*max(0,v['swing']-45)**2+1000*max(0,v['p99']-1.9)**2+100000*max(0,v['reach']-.95)**2 for v in stats.values())+30*(center-Vector((0,-.3,1.2))).length
    rows.append({'score':score,'center':list(center),'axis':list(axis),'stats':stats})
rows.sort(key=lambda r:r['score']);json.dump(rows,open(p/'work/carry_search.json','w'),indent=2)
for row in rows[:8]:print('CARRY_CANDIDATE',json.dumps(row),flush=True)
