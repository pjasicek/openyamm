from pathlib import Path
import os,sys
p=Path(__file__).resolve().parents[1]
os.environ['R_HANDLE']='0.014'
sys.argv=['grip_solve','--',str(p/'work/motion_adapted.blend'),'Standing','0']
exec(compile((p/'scripts/grip_solve.py').read_text().split('grid = np.radians')[0],str(p/'scripts/grip_solve.py'),'exec'))
print('AXIS vs knuckle',np.degrees(np.arccos(np.clip(A@((joints(1)[0]-joints(4)[0])/np.linalg.norm(joints(1)[0]-joints(4)[0])),-1,1))))
for i in (0,1,2,4):
    print('FINGER_COORD',i, [[round(float((q-C)@v)*100,2) for v in (A,fdir,nrm)] for q in joints(i)])
