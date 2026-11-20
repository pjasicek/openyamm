import sys,collections
sys.path.insert(0,'output/studio_cal/mm6_scifi')
from secs import *
def bands(si, floor, ceil, step=16):
    sl=collections.defaultdict(collections.Counter)
    for fi in S[si]['wall_faces']:
        f=F[fi]; lo,hi=bb(f)
        if hi[2]<=lo[2]: continue
        t=f['texture'].lower()
        if t.startswith('ch5') or t in('pending','trekscrn'): continue
        a=area(f)/(hi[2]-lo[2])
        z=floor
        while z<ceil:
            ov=min(hi[2],z+step)-max(lo[2],z)
            if ov>0: sl[z][t]+=a*ov
            z+=step
    out=[]
    z=floor
    while z<ceil:
        if sl[z]:
            t,a=sl[z].most_common(1)[0]
            if out and out[-1][1]==t: out[-1][2]=z+step
            else: out.append([z,t,z+step])
        z+=step
    return [(t,b-floor) for a,t,b in out]
if __name__=='__main__':
    for si in range(1,92):
        s=S[si]
        if not s['floor_faces']: continue
        fl=collections.Counter()
        for fi in s['floor_faces']:
            lo,hi=bb(F[fi]); fl[lo[2]]+=area(F[fi])
        floor=fl.most_common(1)[0][0]
        b=bands(si,floor,s['max'][2]-5)
        if len(b)>1: print(si,floor,b)
