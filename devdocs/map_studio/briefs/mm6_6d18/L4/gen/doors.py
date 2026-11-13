import yaml,json,sys
sys.path.insert(0,'output/studio_cal/mm6_6d18')
s=yaml.safe_load(open('assets_dev/worlds/mm6/maps/6d18.scene.yml'))
d=json.load(open('output/studio_cal/mm6_6d18/orig.json'))['map']
V=d['vertices'];F=d['faces']
for door in s['initial_state']['doors']:
    vi=door.get('vertex_ids') or []
    fi=door.get('face_ids') or []
    ps=[V[i] for i in vi]
    lo=[min(p[k] for p in ps) for k in range(3)] if ps else None
    hi=[max(p[k] for p in ps) for k in range(3)] if ps else None
    tex=sorted(set(F[i]['texture'] for i in fi))
    rooms=sorted(set(F[i]['room'] for i in fi)|set(F[i]['room_behind'] for i in fi))
    print({k:v for k,v in door.items() if not isinstance(v,list)}, 'nv',len(vi),'nf',len(fi),'bb',lo,hi,tex,rooms)
