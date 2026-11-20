import sys; sys.path.insert(0, sys.argv[1])
import geo
for p in sys.argv[2:]:
    m = geo.parse_odm(p) if p.endswith('.odm') else geo.parse_blv(p)
    if m['kind']=='odm':
        print(p, 'bmodels', len(m['bmodels']), 'faces', sum(len(b['faces']) for b in m['bmodels']), 'ents', len(m['entities']), 'spawns', len(m['spawns']), 'tail', m['tail'], m['bmodels'][0]['name'], m['bmodels'][0]['pos'])
    else:
        print(p, 'verts', len(m['verts']), 'faces', len(m['faces']), 'extras', len(m['extras']), 'sectors', m['sector_count'], 'doors', m['door_count'], 'ents', len(m['entities']), 'lights', len(m['lights']), 'spawns', len(m['spawns']), 'outlines', m['outline_count'], 'tail', m['tail'])
