"""Lane S's pieces on the four Elemental Planes (A6, twentieth session, 2026-11-21; D-58 C5/C7): the decorations of
objects.yml and the events that go with them, shared by output/studio_cal/p1-p4/tools/gen.py.

Rows 4023-4042 (assets_dev/worlds/xeen/models/indoor_decorations.yml; level_generation/decorations/xeen_planes_claude,
xeen_sleeper_claude, xeen_wayup_claude). Every binding but the ways up turns by `yaw_offset` -90: the map's `facing`
is the direction the piece's front looks (the sleeper's head lies on the viewer's left).

- the sleeper on his couch: clicked, A3's m38.sleeper_<element> (three states; awake sets the element's qbit);
- the statue: on A6's plinth (the fire statue brings its own plinth and stands on the floor); clicked, the plaque;
- the test pedestal: beside the plate, facing it (no event: the plate asks);
- the return dais: hidden until the sleeper wakes (as `platform:dais`), clicked like the dais;
- the way up's effect (P1-P3; P4's waterspout is geometry): clicked like the way up.

A decoration is clicked through its own event (a click event has one source), so each click on a piece runs the same
body as the platform it covers.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[5])  # the repository root

ELEMENT_NAME = {'fire': 'Fire', 'air': 'Air', 'earth': 'Earth', 'water': 'Water'}


def deco(did, room, name, at, facing=None, floor_height=None, notes=None, **kw):
    e = {'id': f'deco:{did}', 'room': room, 'decoration': name, 'at': [int(round(at[0])), int(round(at[1]))]}
    if facing is not None:
        e['facing'] = int(round(facing)) % 360
    if floor_height is not None:
        e['floor_height'] = int(round(floor_height))
    e.update(kw)
    if notes:
        e['notes'] = notes
    return e


def decorations(el, room, sleeper, statue, pedestal, dais, way_up=None, extra=()):
    """Each spot is (at, facing, floor_height or None: the highest floor there)."""
    E = ELEMENT_NAME[el]
    out = [
        deco('sleeper', room, f'xeen_sleeper_{el}', sleeper[0], sleeper[1], sleeper[2],
             notes=(f"The {E} Sleeper on his couch (S, row 4023-4026; D-58 C7): the head on the left seen from the "
                    f"front; clicked, A3's m38.sleeper_{el}.")),
        deco('statue', room, f'xeen_statue_{el}', statue[0], statue[1], statue[2],
             notes=(f"The statue of {E} (S, D-58 C7)"
                    + (" on its own black plinth with the plaque (row radius 224, solid); clicked, A3's "
                       "m38.plaque_fire." if el == 'fire' else f" on A6's plinth; clicked, A3's m38.plaque_{el}."))),
        deco('pedestal', room, f'xeen_pedestal_{el}', pedestal[0], pedestal[1], pedestal[2],
             notes="The test's pedestal (S): beside the plate, facing it, off the walking line."),
        deco('dais', room, f'xeen_dais_{el}', dais[0], dais[1], dais[2], hidden=True,
             notes=(f"The return dais (S's disc over platform:dais): hidden until the {E} Sleeper wakes "
                    "(evt:dais_load, evt:dais_show).")),
    ]
    if way_up:
        out.append(deco('way_up', room, f'xeen_wayup_{el}', way_up[0], way_up[1], way_up[2],
                        notes="The way up's effect (S, no collision): clicked like the way up."))
    out += list(extra)
    return out


def dais_events(el, qbit_name, show_platform=True):
    """The dais shows the second the sleeper wakes, and on every load after (P-1)."""
    show = ([{'show': 'platform:dais'}, {'solid': 'platform:dais'}] if show_platform else []) + \
        [{'show': 'deco:dais'}, {'set': {'var': {'map_var': 'dais_shown'}, 'value': 1}}]
    return [
        {'id': 'evt:dais_show', 'preset': 'script', 'trigger': 'timer', 'every': 1,
         'condition': {'all': [{'qbit': qbit_name}, {'not': {'map_var': 'dais_shown'}}]},
         'effects': show,
         'notes': f"The dais rises the second the {ELEMENT_NAME[el]} Sleeper wakes ({qbit_name})."},
        {'id': 'evt:dais_load', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': qbit_name},
         'effects': show,
         'notes': f"P-1: the dais shown on every load once {qbit_name} is set (S's disc starts hidden)."},
    ]


def sleeper_event(el):
    return {'id': 'evt:sleeper', 'preset': 'script', 'source': 'deco:sleeper',
            'title': f'The {ELEMENT_NAME[el]} Sleeper', 'lua': f'XeenQuests.hook("m38.sleeper_{el}")',
            'notes': (f"A3's m38.sleeper_{el} (clicked, every time): not Chosen; 'Awaiting Grunfeld field "
                      "activation.'; awake (the qbit, the award, 10,500 experience).")}


def copy_for(ev, did, eid):
    """The same click on a decoration that covers the platform."""
    e = {k: v for k, v in ev.items() if k not in ('id', 'source', 'notes')}
    e['id'] = eid
    e['source'] = f'deco:{did}'
    e['notes'] = f"{ev['id']} clicked on S's decoration over it."
    return e


RETURN = {'fire': (-27456, 17728), 'air': (27456, 17728), 'earth': (27136, -17408), 'water': (-27456, -17728)}
SLEEPER_QBIT = {'fire': 111760, 'air': 111761, 'earth': 111762, 'water': 111763}
TEST_QBIT = {'fire': 111764, 'air': 111765, 'earth': 111766, 'water': 111767}
REFLECTORS = (111740, 111741, 111742, 111743)     # m37.air/fire/earth/water
CHOSEN = 409                                      # m30.chosen


def sleeper_steps(el, mapname, head, ids, near, yaw):
    """The sleeper's three answers by a click on S's couch, the dais hidden until he wakes, shown the second he does,
    kept over a save and reload, then Yes on the dais to D7's entrance:p<n>_return. `near`: (x, y, z) beside the couch;
    `ids`: the build's ids.lock.yml."""
    E = ELEMENT_NAME[el]
    ev, dec = ids['events'], ids['decorations']
    dais = dec['deco:dais']

    def click(name):
        return {'play_lua': {'source': f'click({ev[name]}); wait(0.5)'}}

    def says(text):     # s32: the sleepers' lines are status lines since D-90 (A3's hooks)
        return {'play_lua': {'source': "local s = status(); if not string.find(s, %r, 1, true) then "
                                       "error('status: ' .. s) end" % text}}

    close = {'play_lua': {'source': 'close(); wait(0.3); close()'}}
    s = head()
    s += [{'setup_shortcut': {'kind': 'set_qbit', 'id': TEST_QBIT[el], 'value': True}},
          {'clear_hostiles': {'radius': 40000}},
          {'set_pose': {'map': mapname, 'x': int(near[0]), 'y': int(near[1]), 'z': int(near[2]), 'yaw_degrees': yaw,
                        'pitch': 0}},
          {'advance_runtime': {'seconds': 1.5}},
          {'assert': {'sprite_hidden': [dais]}},
          {'note': f"Not Chosen: the {E} Sleeper cannot wake (A3's first state); the dais stays dark"},
          click('evt:sleeper'), says('has not informed me'), close,
          {'play_lua': {'source': (f"click({ev['evt:dais']}); wait(0.5); local s = status() or ''; "
                                   "if not s:find('dark and still') then error('dais before the wake: ' .. s) end")}},
          {'assert': {'map': mapname}},
          {'note': "Chosen, the Reflectors not all humming: 'Awaiting Grunfeld field activation.'"},
          {'lua_event': {'source': f'evt.ForPlayer(Players.All)\nSetAward(Award({CHOSEN}))'}},
          click('evt:sleeper'), says('Awaiting Grunfeld field activation'), close,
          {'assert': {'qbit_clear': [SLEEPER_QBIT[el]]}}]
    s += [{'setup_shortcut': {'kind': 'set_qbit', 'id': q, 'value': True}} for q in REFLECTORS]
    s += [{'note': f"All four humming: he wakes ({SLEEPER_QBIT[el]}), the dais rises at once"},
          click('evt:sleeper'), says('Grunfeld field generator is active'), close,
          {'assert': {'qbit_set': [SLEEPER_QBIT[el]]}},
          {'advance_runtime': {'seconds': 2.5}},
          {'assert': {'sprite_shown': [dais]}},
          {'note': 'A save and a reload: the dais still shown'},
          {'reload': {}}, {'advance_runtime': {'seconds': 2}},
          {'assert': {'sprite_shown': [dais]}},
          {'note': "S's disc and the dais both ask; No stays, Yes up to D7"},
          click('evt:dais_disc'), {'assert': {'dialog': {'active': True, 'action_label_present': 'Close'}}}, {'select_topic': {'match_label': 'Close'}},
          {'advance_runtime': {'seconds': 1.0}}, {'assert': {'map': mapname}}, close,
          click('evt:dais'), {'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}}, {'select_topic': {'match_label': 'OK'}},
          {'advance_runtime': {'seconds': 2.0, 'follow_map_move': True}},
          {'assert': {'map': 'xeen_d7.blv'}},
          {'assert': {'party_position': {'x': RETURN[el][0], 'y': RETURN[el][1], 'radius': 256}}}]
    return s


def notes_section(el, extra=()):
    """The L4 NOTES section on S's pieces (session 20)."""
    E = ELEMENT_NAME[el]
    T = ["## S's pieces (twentieth session, 2026-11-21)\n",
         f"- The {E} Sleeper on his couch (`xeen_sleeper_{el}`, row radius 290): clicked, A3's `m38.sleeper_{el}` "
         "(its three answers; awake sets the qbit, the award and 10,500 experience).",
         "- The statue " + ("on its own black plinth, its plaque `m38.plaque_fire` clicked on the decoration (radius 224)"
                            if el == 'fire' else f"on A6's plinth (`m38.plaque_{el}` on the plinth and on the statue)")
         + "; the test's pedestal 208 from its plate's centre, facing it.",
         "- The return dais: S's disc on the studio disc's top, both hidden until the sleeper wakes; the dais rises "
         "the second the qbit is set (`evt:dais_show`, a 1-s timer) and on every load after (`evt:dais_load`); "
         "clicked on either, the dais's question and D7's return.",
         "- Every binding turns by `yaw_offset` -90 (`facing` is where the front looks; the sleeper's head on the "
         "viewer's left). New playtest `playtest_sleeper` (the three answers, the dais hidden then shown, kept over "
         "a reload, Yes to D7)."]
    T += list(extra)
    return T + ['']


def d7_return_lua(el):
    """s32 (F16): the way up and the dais into D7 (a BLV) as a move with the standard entrance window (picture 1), no
    Yes/No of the map's own; D7's entrance:p<n>_return from its installed studio sidecar."""
    import os
    import yaml
    side = yaml.safe_load(open(os.path.join(_REPO_ROOT + '/assets_dev/worlds/xeen/maps',
                                            'xeen_d7.studio.yml')))
    name = 'entrance:p%d_return' % (1 + ['fire', 'air', 'earth', 'water'].index(el))
    a = next(a for a in side['arrivals'] if a.get('name', a.get('id')) == name)
    return 'evt.MoveToMap(%d, %d, %d, %d, 0, 0, 0, 1, "xeen_d7.blv")' % (*a['at'], int(a['facing']))
