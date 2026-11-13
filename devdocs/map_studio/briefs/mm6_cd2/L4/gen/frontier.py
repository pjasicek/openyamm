import json,subprocess,sys
R='/home/pjasicek/github/OpenYAMM/'
L=R+'devdocs/map_studio/briefs/mm6_cd2/L4'
d=json.loads(subprocess.run([R+'openyamm-studio/build/oymap','solve',L,'--assets',R+'assets_dev','--json'],capture_output=True,text=True).stdout)
g=json.load(open(R+'output/studio_cal/mm6_cd2/gen_rooms.json'))
reach0=set(d['sector_rooms'][str(n)] for w in d['waves'] for n in w['sectors'])
rooms={r['id']:r for r in g['rooms']}
reached=reach0
print('reached',len(reached),'of',len(rooms),'; sectors reached',len(set(rooms[r]['sector'] for r in reached)),'of',len(set(r['sector'] for r in g['rooms'])))
for o in g['openings']:
    a,b=o['from'],o['to']
    if (a in reached)!=(b in reached):
        ra,rb=rooms[a],rooms[b]
        print('  blocked %s: %s (floor %s..%s) | %s (floor %s..%s) w=%s h=%s sill=%s %s'%(o['id'],a,ra['floor'],ra['floor_high'],b,rb['floor'],rb['floor_high'],o.get('width'),o.get('height'),o.get('sill',0),o.get('notes','')))
linked=set()
for o in g['openings']: linked.add(o['from']);linked.add(o['to'])
print('rooms without any opening:',sorted(set(rooms)-linked))
un=collections_un=sorted(set(rooms[r]['sector'] for r in rooms)-set(rooms[r]['sector'] for r in reached))
print('sectors with no reached room:',un)
print('unreached rooms:',' '.join(sorted(r.split(':')[1] for r in set(rooms)-reached)))
