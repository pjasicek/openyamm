import json,sys,collections
d=json.load(open('output/studio_cal/mm6_scifi/orig.json'))['map']
V=d['vertices'];F=d['faces'];S=d['sectors']
def area(f):
    p=[V[i] for i in f['vertices']]
    ax=ay=az=0
    for i in range(1,len(p)-1):
        a=[p[i][k]-p[0][k] for k in range(3)];b=[p[i+1][k]-p[0][k] for k in range(3)]
        ax+=a[1]*b[2]-a[2]*b[1];ay+=a[2]*b[0]-a[0]*b[2];az+=a[0]*b[1]-a[1]*b[0]
    return (ax*ax+ay*ay+az*az)**.5/2
def bb(f):
    p=[V[i] for i in f['vertices']]
    return [min(q[k] for q in p) for k in range(3)],[max(q[k] for q in p) for k in range(3)]
if __name__=='__main__':
  sel=[int(x) for x in sys.argv[1:]] or range(len(S))
  for si in sel:
    s=S[si]
    if not s['faces']: continue
    print(f"== S{si} min{s['min']} max{s['max']} amb{s['min_ambient_light_level']} faces{s['face_count']}")
    fl=collections.Counter();flt=collections.Counter()
    for fi in s['floor_faces']:
        f=F[fi];lo,hi=bb(f)
        key=(lo[2],hi[2]) ; fl[key]+=area(f); flt[f['texture'].lower()]+=area(f)
    print("  floors z:", {k:int(v) for k,v in sorted(fl.items())}, dict((k,int(v)) for k,v in flt.most_common(3)))
    cl=collections.Counter();clt=collections.Counter()
    for fi in s['ceiling_faces']:
        f=F[fi];lo,hi=bb(f); cl[(lo[2],hi[2])]+=area(f); clt[f['texture'].lower()]+=area(f)
    print("  ceil z:", {k:int(v) for k,v in sorted(cl.items(),key=lambda x:-x[1])[:6]}, dict((k,int(v)) for k,v in clt.most_common(3)))
    wt=collections.Counter()
    for fi in s['wall_faces']:
        f=F[fi]; wt[f['texture'].lower()]+=area(f)
    print("  walls:", dict((k,int(v)) for k,v in wt.most_common(5)))
    for fi in s['portal_faces']:
        f=F[fi];lo,hi=bb(f); o=f['room_behind'] if f['room']==si else f['room']
        print(f"  portal f{fi} -> S{o} {lo} {hi}")
