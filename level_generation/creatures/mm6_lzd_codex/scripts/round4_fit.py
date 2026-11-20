from pathlib import Path
import sys
P=Path(__file__).resolve().parents[1]
exec((P/'scripts/round4_author.py').read_text().split('rest();home=get()')[0])
sys.path.insert(0,str(P.parents[2]/'level_generation/creatures/claude_shared/gates'))
from run_gates import swing_twist,angle
carryR=carryR@Matrix.Rotation(math.pi,3,"Y")
originG=G.copy();out=[]
for deg in range(-180,181,10):
 G=originG@Matrix.Rotation(math.radians(deg),4,'Z')
 rest()
 s='L';U,F,H=[f'B_{s}_{n}'for n in ['UpperArm','Forearm','Hand']]
 up,fp,hp=[rig.pose.bones[n].matrix.to_3x3()for n in [U,F,H]]
 ax=sum((rb[f'B_L_Finger{i}'].head_local for i in [0,1,2,2,4]),Vector())/5-rb[H].head_local
 sw,tw=swing_twist(np.array((fp@R0[F].inverted()@R0[H]).inverted()@hp),np.array(R0[H].inverted()@ax.normalized()))
 out.append([deg,float(sw),float(tw)])
print('FIT',out,flush=True)
