"""Camera strings for vshots: cam.py x,y,z dx,dy,dz dist -> 'camx,camy,camz:tx,ty,tz'"""
import sys, numpy as np
t=np.array(sys.argv[1].split(','),float); d=np.array(sys.argv[2].split(','),float); d/=np.linalg.norm(d); D=float(sys.argv[3]); c=t+d*D
print(','.join(f'{x:.3f}' for x in c)+':'+','.join(f'{x:.3f}' for x in t))
