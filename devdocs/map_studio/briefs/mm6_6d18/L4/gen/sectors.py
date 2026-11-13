import json,collections,sys
d=json.load(open('output/studio_cal/mm6_6d18/orig.json'))['map']
V=d['vertices'];F=d['faces']
def area(f):
    p=[V[i] for i in f['vertices']];n=len(p);a=[0,0,0]
    for i in range(1,n-1):
        u=[p[i][k]-p[0][k] for k in range(3)];w=[p[i+1][k]-p[0][k] for k in range(3)]
        a[0]+=u[1]*w[2]-u[2]*w[1];a[1]+=u[2]*w[0]-u[0]*w[2];a[2]+=u[0]*w[1]-u[1]*w[0]
    return (a[0]**2+a[1]**2+a[2]**2)**.5/2
def bb(f):
    p=[V[i] for i in f['vertices']]
    return [min(q[k] for q in p) for k in range(3)],[max(q[k] for q in p) for k in range(3)]
if __name__=='__main__':
  pass
  for si,s in enumerate(d['sectors']):
    if not s['faces'] and not s['floor_faces']: continue
    print(f"--- sector {si} min {s['min']} max {s['max']} amb {s['min_ambient_light_level']} faces {s['face_count']} lights {len(s['lights'])} decs {len(s['decorations'])}")
    fl=collections.Counter();ce=collections.Counter();wa=collections.Counter()
    for fi in s['floor_faces']:
        f=F[fi];lo,hi=bb(f);fl[(f['texture'],lo[2],hi[2],f['cog_triggered'],hex(f['attributes']))]+=area(f)
    for fi in s['ceiling_faces']:
        f=F[fi];lo,hi=bb(f);ce[(f['texture'],lo[2],hi[2])]+=area(f)
    for fi in s['wall_faces']:
        f=F[fi];wa[f['texture']]+=area(f)
    print(' floors',[(k,int(v)) for k,v in sorted(fl.items(),key=lambda x:-x[1])][:8])
    print(' ceils',[(k,int(v)) for k,v in sorted(ce.items(),key=lambda x:-x[1])][:5])
    print(' walls',[(k,int(v)) for k,v in sorted(wa.items(),key=lambda x:-x[1])][:6])
