import yaml,json,collections
s=yaml.safe_load(open('assets_dev/worlds/mm6/maps/hive.scene.yml'))
d=json.load(open('output/studio_cal/mm6_hive/orig.json'))['map']
V=d['vertices'];F=d['faces']
for dr in sorted(s['initial_state']['doors'],key=lambda x:x['door_id']):
    vs=[V[i] for i in dr['vertex_ids']]
    if not vs: print('door',dr['door_id'],'no verts');continue
    mn=[min(v[k] for v in vs) for k in range(3)];mx=[max(v[k] for v in vs) for k in range(3)]
    dirn=[round(dr['direction'][k]/65536,2) for k in 'xyz']
    tex=collections.Counter(F[i]['texture'].lower() for i in dr['face_ids'])
    ev=collections.Counter((F[i]['cog_number'],F[i]['cog_triggered'],F[i]['cog_trigger_type']) for i in dr['face_ids'])
    print(f"door {dr['door_id']} state={dr['state']} attr={dr['legacy_attributes']} dir={dirn} len={dr['move_length']} spd={dr['open_speed']}/{dr['close_speed']} bbox={mn}..{mx} nv={len(vs)} nf={len(dr['face_ids'])} sect={dr['sector_ids']} tex={dict(tex.most_common(3))} cog={dict(ev)}")
print()
# faces with events
ev=collections.defaultdict(list)
for i,f in enumerate(F):
    if f['cog_triggered']:
        p=[V[v] for v in f['vertices']]
        c=[sum(q[k] for q in p)//len(p) for k in range(3)]
        ev[f['cog_triggered']].append((i,f['room'],c,f['facet_type'],f['texture'].lower(),f['cog_trigger_type'],f['attributes']))
for e in sorted(ev):
    l=ev[e]
    print('event',e,len(l),'faces', l[:4])
print('entities',d['entities'])
for c in s['initial_state']['actors']: print('actor',c['monster_id'],c['monster_info_id'],c['position'],c['sector_id'],c['hp'],c['group'])
for c in s['initial_state']['sprite_objects']: print('sprite',c['sprite_id'],c['position'],c['raw_containing_item_hex'][:16])
for c in s['initial_state']['chests']:
    if c['raw_items_hex'].strip('0F A') or True:
        import re
        h=c['raw_items_hex']; n=len(h)
        print('chest',c['chest_index'],c['chest_type_id'],c['flags'], 'nonzero bytes', sum(1 for i in range(0,n,2) if h[i:i+2] not in('00',)))
import collections as C
print(C.Counter((sp['type_id'],sp['index']) for sp in s['spawns']))
