import sys,collections
sys.path.insert(0,'output/studio_cal/mm6_scifi')
from outl import *
def levels(si,kind='floor_faces',tol=20):
    g=collections.defaultdict(list)
    for fi in S[si][kind]:
        lo,hi=bb(F[fi]); g[(lo[2],hi[2])].append(fi)
    for k in sorted(g):
        ls=[simp(l,tol) for l in loops_of(g[k])]
        tx=collections.Counter(F[fi]['texture'].lower() for fi in g[k])
        for l in ls:
            if abs(parea(l))<1000: continue
            xs=[p[0] for p in l];ys=[p[1] for p in l]
            print(f"  z{k} {dict(tx)} n{len(l)} area{int(parea(l))} bbox[{min(xs)},{min(ys)}..{max(xs)},{max(ys)}]: {[list(p) for p in l] if len(l)<=40 else '...'}")
if __name__=='__main__':
    kind=sys.argv[1]
    for a in sys.argv[2:]:
        print('S'+a,kind); levels(int(a),kind)
