#!/usr/bin/env python3
"""X4 Burlock Savannah: writes every level of the brief (A5, 2026-11-20).

    gen.py [briefs folder]      (default devdocs/xeen/briefs/x4)

L1 is the approved MU-3 plan with D-11.2/5/6 (gen_l1.py writes it); L2 the specification (plan without the sketch);
L3 the plan with the full sketch; L4 the same, built and installed (ids.lock.yml beside it after a build). The land
is land.py, the towns' plots, structures, actors and events places.py, the scatter scatter.py. Edit those and run
../vw.sh, never the YAML.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import copy
import os
import sys
sys.path.insert(0, _REPO_ROOT + '/tools/xeen')
import villagers as V  # noqa: E402  D-96 (A4, F20): each settlement's street villagers, source/towns/villagers.yml

import yaml

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import gen_l1 as L1          # noqa: E402
import land as LD            # noqa: E402
import places as P           # noqa: E402
import scatter as SC         # noqa: E402

BRIEFS = sys.argv[1] if len(sys.argv) > 1 else 'devdocs/xeen/briefs/x4'

# neighbours kept while their maps are not installed are dropped with their ways in (the A5 rule: no exit into an
# unbuilt or MM7 map; a sealed door says a line instead)
LIVE = {'edge:south_x2': True, 'door:xd02_adit': True, 'edge:south_x3': P.X3_LIVE, 'edge:west': P.X6_LIVE,
        'edge:east': P.X7_LIVE,
        'door:xd07': P.XD07_LIVE, 'fall:xd07_throne': P.XD07_LIVE, 'door:xd25': P.XD25_LIVE, 'door:xd26': P.XD26_LIVE,
        'door:xd26_sky_crack': P.XD26_LIVE}


def project():
    pr = copy.deepcopy(L1.PROJECT)
    pr['map_stats']['slots'][0]['monster'] = P.KNIGHT_SLOT
    neigh = []
    for n in pr['neighbours']:
        if not LIVE.get(n['id'], True):
            continue
        n = dict(n)
        if n['kind'] in ('stable', 'boat'):
            n['listed_only'] = True
        inside = {'door:xd07': P.XD07_ARRIVAL, 'door:xd25': P.XD25_ARRIVAL, 'door:xd26': P.XD26_ARRIVAL}
        if n['id'] in inside:
            n['arrival'] = list(inside[n['id']][:3])
            n['direction'] = inside[n['id']][3]
        if n['id'] == 'edge:south_x3':
            # D-11.6: one side, two maps: X3 west of x 0, X2 (the side's own neighbour and travel row) east of it
            n['span'] = [-32768, 0]
            n['arrival'] = list(P.X3_ARRIVAL[:3])
            n['direction'] = P.X3_ARRIVAL[3]
        if n['id'] == 'edge:west':
            # X6's east arrival (A2's edge_spans row: X4 west -> X6 (22016, 2048, 1216) facing 1024)
            n['arrival'] = list(P.X6_ARRIVAL[:3])
            n['direction'] = P.X6_ARRIVAL[3]
            n['notes'] = 'X6 Desert of the Sphinx (a wilderness edge, 7 days): the desert road at y 60.'
        if n['id'] == 'edge:east':
            n['arrival'] = list(P.X7_ARRIVAL[:3])
            n['direction'] = P.X7_ARRIVAL[3]
            n['notes'] = "X7 Mount Firestone (D-40, 5 days): the Firestone road at y 66 to X7's entrance:west_road."
        if n['id'] == 'door:xd02_adit':
            n['arrival'] = list(P.XD02_ADIT_ARRIVAL[:3])
            n['direction'] = P.XD02_ADIT_ARRIVAL[3]
            n['notes'] = ("XD-02's west adit (M3): X4's door leads to the adit's end inside XD-02 (its collapsed adit, "
                          "past the fall the winch drags away), facing east into the mine; open with qbit 110020. "
                          "DOORS.md.")
        neigh.append(n)
    pr['neighbours'] = neigh
    pr['rules'] = {'weather': 'fair', 'respawn': 'entrance:burlock_square',
                   'town_portal_anchor': 'entrance:burlock_square'}
    pr['notes'] = ("X4 Burlock Savannah (A5, 2026-11-20): Castle Burlock's village and the castle rise (XD-07's gate), "
                   "the lists, Asp with the pedestals (D-4), the Autumn Druid's grove, the eyrie (XD-26), the undercroft "
                   "(XD-25), XD-02's west adit. Written by output/studio_cal/x4/tools/gen.py; NOTES.md in L4.")
    return pr


def plan(level):
    p = L1.plan()
    p['level'] = level
    p['spaces'].append({'id': 'water:tarn', 'name': 'The tarn above the falls', 'kind': 'water',
                        'part_of': 'zone:gargoyle_range', 'purpose': 'A tarn high in the range that spills over the falls.'})
    gone = {k for k, v in LIVE.items() if not v}
    p['entrances'] = [e for e in p['entrances'] if e.get('neighbour') not in gone]
    for e in p['entrances']:
        if 'neighbours' in e:
            e.pop('neighbours')
    p['notes'] = ('Written by output/studio_cal/x4/tools/gen.py from gen_l1.py (the approved L1 with D-11.2/5/6). '
                  'Sealed (their neighbours dropped until the maps exist): ' + ', '.join(sorted(gone)) + '.')
    if level == 'L2':
        p.pop('sketch', None)
    return p


def sketch():
    s = L1.sketch()
    gone = {k for k, v in LIVE.items() if not v}
    gone_points = {'entrance:x3_road': 'edge:south_x3', 'entrance:west_road': 'edge:west',
                   'entrance:east_road': 'edge:east', 'entrance:xd07_gate': 'door:xd07',
                   'entrance:throne_landing': 'fall:xd07_throne', 'entrance:xd25_stair': 'door:xd25',
                   'entrance:xd26_eyrie': 'door:xd26', 'entrance:xd26_sky_crack': 'door:xd26_sky_crack'}
    s['points'] = [q for q in s['points'] if gone_points.get(q['id']) not in gone]
    s['frame']['edges'] = [e for e in s['frame']['edges'] if e['neighbour'] not in gone]
    s['heights'] = LD.heights()
    s['heights'].setdefault('nodes', []).append(P.XD25_CUT.nodes())   # D-95: the undercroft stair's cut
    s['water'] = LD.water()
    s['roads'] = LD.roads()
    s['ground'] = LD.ground()
    for d in s['districts']:
        if d['space'] in P.plots_by_space:
            d['plots'] = P.plots_by_space[d['space']]
    s['structures'] = P.structures()
    s['actors'] = V.fill(P.actors(), 'X4')   # D-96: Burlock's and Asp's villagers
    s['events'] = P.events()
    s['scatter'] = SC.scatter()
    rel = (P.relations() or []) + V.relations('X4')
    if rel:
        s['relations'] = rel
    s['notes'] = ('X4 Burlock Savannah, L3/L4 sketch (A5, 2026-11-20), written by output/studio_cal/x4/tools/gen.py. '
                  'Cells [x, y], x east, y south. Heights above the stars below the north rim (0): the river 640, the '
                  'savannah 950-1,350, the village 1,312, the castle rise 1,888, the range to 3,900.')
    return s


def dump(folder, name, data):
    if name == 'sketch.yml':   # AU's outdoor beds (A5, 2026-11-21; level_generation/projects/xeen/common/beds)
        sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/common/beds')
        import beds as _beds
        data = _beds.with_beds(data, 'x4')
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, name), 'w') as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=120)


def main():
    L1.main()
    pr = project()
    sk = sketch()
    # F2/F8 (2026-11-21) + F16 (A5 s29, 2026-11-22): wing doors as double doors, the Eyrie's mouth as wide as its rim,
    # the entrance window's trans.txt lines
    sys.path.insert(0, _REPO_ROOT + '/tools/xeen')
    sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/common')
    import house_doors as HD
    import entrance as EN
    for _note in HD.double_doors_sketch(sk) + HD.bury_mouths_sketch(sk) + EN.apply(sk, 'x4'):
        print('door:', _note)
    # P2 feedback F29/F32/F33 (agent xeen-fb2-wild, 2026-11-23): shrine altars, campfires, the rim fall
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'common'))
    import wild as WILD
    for _note in WILD.apply(sk, 'x4'):
        print('wild:', _note)
    # Texture fit (merge point 16): the base course (foundation 128) falls back to the wall; the plaster kit's
    # half-timber panel hhm2b2 then shows 1.5 times up a one-storey wall. A dark seamless stone footing instead.
    for district in sk['districts']:
        for plot in district.get('plots', []):
            if plot.get('kit') == 'plaster':
                plot.setdefault('textures', {}).setdefault('base', 'cwb1')
    for thing in sk['structures']:
        if thing.get('kind') == 'building' and thing.get('kit') == 'plaster':
            thing.setdefault('textures', {}).setdefault('base', 'cwb1')
    atmos = {'format': 0, 'notes': 'Fair sky (shipped preset), a dry tint; the world default weather.'}
    for level in ('L2', 'L3', 'L4'):
        out = os.path.join(BRIEFS, level)
        dump(out, 'project.yml', pr)
        dump(out, 'plan.yml', plan('L3' if level == 'L4' else level))
        if level != 'L2':
            dump(out, 'sketch.yml', sk)
            dump(out, 'atmosphere.yml', atmos)
    print('plots', sum(len(v) for v in P.plots_by_space.values()), 'structures', len(sk['structures']),
          'actors', len(sk['actors']), 'scatter', len(sk['scatter']))


if __name__ == '__main__':
    main()
