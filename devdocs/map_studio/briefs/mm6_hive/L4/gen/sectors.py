import json,collections,sys
d=json.load(open('output/studio_cal/mm6_hive/orig.json'))['map']
V=d['vertices'];F=d['faces'];S=d['sectors']
def area(pts):
    a=0
    for i in range(len(pts)):
        x1,y1=pts[i][:2];x2,y2=pts[(i+1)%len(pts)][:2];a+=x1*y2-x2*y1
    return abs(a)/2
for si,s in enumerate(S):
    if not s['faces']: continue
    fl=[F[i] for i in s['floor_faces']]
    fz=[];fa=0;tex=collections.Counter()
    for f in fl:
        p=[V[v] for v in f['vertices']];a=area(p);fa+=a;fz+= [q[2] for q in p];tex['F:'+f['texture'].lower()]+=a
    cz=[]
    for i in s['ceiling_faces']:
        f=F[i];p=[V[v] for v in f['vertices']];cz+=[q[2] for q in p];tex['C:'+f['texture'].lower()]+=area(p)
    for i in s['wall_faces']:
        f=F[i];tex['W:'+f['texture'].lower()]+=1
    nb=[]
    for i in s['portal_faces']:
        f=F[i];o=f['room_behind'] if f['room']==si else f['room'];p=[V[v] for v in f['vertices']]
        xs=[q[0] for q in p];ys=[q[1] for q in p];zs=[q[2] for q in p]
        nb.append(f"{o}@({(min(xs)+max(xs))//2},{(min(ys)+max(ys))//2},{min(zs)}..{max(zs)} w{max(max(xs)-min(xs),max(ys)-min(ys))})")
    t=' '.join(f"{k}" for k,v in tex.most_common(5))
    print(f"S{si} x{s['min'][0]}..{s['max'][0]} y{s['min'][1]}..{s['max'][1]} z{s['min'][2]}..{s['max'][2]} floorA={fa/1e3:.0f}k fz={min(fz) if fz else None}..{max(fz) if fz else None} cz={min(cz) if cz else None}..{max(cz) if cz else None} nf={s['face_count']} amb={s['min_ambient_light_level']}\n    nb: {' '.join(nb)}\n    tex: {t}")
