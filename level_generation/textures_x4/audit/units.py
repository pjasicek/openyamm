"""Candidate split pictures in one world: chains of pixel-continuous joints between exclusive partners."""
import sys, json
sys.path.insert(0, '/home/pjasicek/github/OpenYAMM/level_generation/textures_x4')
import tex
sys.path.insert(0, str(tex.ROOT / 'util'))
from map_export import parse_blv_file, parse_odm_file
world = sys.argv[1]
data = tex.load_json(tex.INVENTORY); textures = {e['id']: e for e in data['textures']}
abut = {}
for mp in sorted((tex.ROOT / 'assets_dev/worlds' / world / 'maps').glob('*.[bo][ld][vm]')):
    indoor = mp.suffix == '.blv'
    pl = (parse_blv_file if indoor else parse_odm_file)(mp)['payload']
    for V, F in ([(pl['vertices'], pl['faces'])] if indoor else [(m['vertices'], m['faces']) for m in pl['bmodels']]):
        tex.collect_abutments(V, F, indoor, abut)
by_name = {e['name']: e for e in textures.values() if e['world'] == world}
for n, e in by_name.items(): e['abutments'] = abut.get(n, [])
links, good = tex.continuous_links(textures, world, by_name)
# all-link partner sets per side (any abutment counts against exclusivity)
nexts, prevs = {}, {}
for (a, b, axis) in links:
    nexts.setdefault((a, axis), set()).add(b); prevs.setdefault((b, axis), set()).add(a)
chains = []
for axis in 'uv':
    g = [(a, b) for (a, b, ax) in good if ax == axis
         and nexts.get((a, axis)) == {b} and prevs.get((b, axis)) == {a}
         and not textures[a].get('assembly') and not textures[b].get('assembly')]
    nxt = dict(g); prv = {b: a for a, b in g}
    for a in nxt:
        if a in prv: continue
        chain = [a]
        while chain[-1] in nxt and nxt[chain[-1]] not in chain: chain.append(nxt[chain[-1]])
        size = list(textures[chain[0]]['size']); along = 0 if axis == 'u' else 1
        size[along] = sum(textures[m]['size'][along] for m in chain)
        chains.append({'members': chain, 'axis': axis, 'size': size,
                       'fits': tex.scale_for(size[0] + 64 * (axis == 'u'), size[1] + 64 * (axis == 'v')) >= tex.SCALE})
for c in chains: print(c['axis'], c['size'], 'fits' if c['fits'] else 'TOO BIG', ' | '.join(m.split('/')[1] for m in c['members']))
json.dump(chains, open(f'./units_{world}.json', 'w'))
