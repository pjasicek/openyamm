import json,sys,collections
d=json.load(open('/home/pjasicek/github/OpenYAMM/output/studio_cal/mm8_d05/orig.json'))['map']
V=d['vertices'];F=d['faces'];SE=d['sectors']
def area(f):
    p=[V[i] for i in f['vertices']]
    ax=ay=az=0
    for i in range(len(p)):
        a=p[i];b=p[(i+1)%len(p)]
        ax+=a[1]*b[2]-a[2]*b[1];ay+=a[2]*b[0]-a[0]*b[2];az+=a[0]*b[1]-a[1]*b[0]
    return (ax*ax+ay*ay+az*az)**.5/2
if __name__=='__main__':
    print([k for k in d.keys()])
    print('doors' in d, json.dumps(d.get('doors',[None])[0])[:1500] if 'doors' in d else '')
    for i,s in enumerate(SE):
        if not s['face_count']: print(i,'empty');continue
        fl=collections.Counter();ce=collections.Counter();tx=collections.Counter()
        for fi in s['floor_faces']:
            f=F[fi];zs=[V[v][2] for v in f['vertices']]
            zs and fl.__setitem__((min(zs),max(zs)),0) if False else None
            if not zs: continue
            fl[(min(zs),max(zs))]+=round(area(f))
        for fi in s['ceiling_faces']:
            f=F[fi];zs=[V[v][2] for v in f['vertices']]
            if not zs: continue
            ce[(min(zs),max(zs))]+=round(area(f))
        for fi in s['faces'] if s['faces'] else s['floor_faces']+s['wall_faces']+s['ceiling_faces']:
            tx[F[fi]['texture']]+=round(area(F[fi]))
        pr=[]
        for fi in s['portal_faces']:
            f=F[fi];p=[V[v] for v in f['vertices']]
            o=f['room_behind'] if f['room']==i else f['room']
            pr.append((o,[min(q[k] for q in p) for k in range(3)],[max(q[k] for q in p) for k in range(3)]))
        print(f"S{i} min{s['min']} max{s['max']} faces{s['face_count']} amb{s['min_ambient_light_level']}")
        print('   floors',fl.most_common(6))
        print('   ceils',ce.most_common(5))
        print('   tex',tx.most_common(6))
        for p in pr: print('   portal->',p)
