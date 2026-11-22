#!/usr/bin/env python3
"""XD-02 second pass, step 8: what a player reads. Hanging braziers hang from beams or become standing pole torches
(dec56); the cocoon is a web-wrapped bundle beside the miner's chest (a ch1 named Chest), the noose corpse a lying
skeleton; the flooded working's vein on a wall seen from the planks; no silent clicks (veins, winch, brake say what
is left); long lines shortened to the status bar or made message windows; the clan's sign a message window; the
brake and the west adit tell where their remedy is. Run once."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
import sys

sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/xd02/pass2')
import yio

L = _REPO_ROOT + '/devdocs/xeen/briefs/xd02/L4/'
R = yio.load(L + 'rooms.yml')
O = yio.load(L + 'objects.yml')
W = yio.load(L + 'wiring.yml')


def room(rid):
    return next(r for r in R['rooms'] if r['id'] == rid)


def obj(col, oid):
    return next(o for o in O[col] if o['id'] == oid)


def evt(eid):
    return next(e for e in W['events'] if e['id'] == eid)


# ---------------------------------------------------------------- braziers
d = obj('decorations', 'deco:top_station_13')
d.update({'at': [12096, 4880], 'height': 300, 'hangs': True})
d = obj('decorations', 'deco:mess_hall_54')
d.update({'at': [8160, 6560], 'height': 300, 'hangs': True})
d = obj('decorations', 'deco:mess_hall_55')
d.update({'at': [8640, 6560], 'height': 300, 'hangs': True})
for did in ('deco:turntable_42', 'deco:turntable_43', 'deco:dwarf_shrine_49', 'deco:dwarf_shrine_50'):
    obj('decorations', did)['decoration'] = 'dec56'

# ---------------------------------------------------------------- the cocoon and the miner's chest
c = obj('chests', 'chest:cocoon')
for k in ('surface', 'top_surface', 'size'):
    c.pop(k, None)
c.update({'kind': 'ch1', 'at': [3330, 1270], 'facing': 'e'})
c['notes'] = "The cocooned miner's chest, beside him in the web."
evt('evt:chest_cocoon')['title'] = 'Chest'
sg = room('room:spider_galleries')
sg.setdefault('platforms', []).append(
    {'rise': 64, 'surface': {'texture': 'xnweb', 'size': [128, 128]}, 'top_surface': {'texture': 'xnweb', 'size': [128, 128]},
     'outline': [[3240, 1090], [3300, 1050], [3390, 1060], [3420, 1120], [3360, 1170], [3270, 1160]],
     'notes': 'The cocooned miner: a body wrapped in thick old web on the floor.'})
d = obj('decorations', 'deco:spider_galleries_102')
d.update({'decoration': 'dec05', 'at': [3480, 1200]})

# ---------------------------------------------------------------- the flooded working's vein, seen from the planks
v = obj('switches', 'switch:vein_flooded')
v.update({'wall': 6, 'along': 0.2})
v['notes'] = "Gold vein in the flooded working's east wall, over the water at the end of the planks."
obj('lights', 'light:glint_flooded')['at'] = [12620, 1178]

# ---------------------------------------------------------------- the clan's warning: a message window
e = evt('evt:clan_sign')
e['title'] = 'Warning sign'
e['window'] = True

# ---------------------------------------------------------------- no silent clicks
W['variables'] = ['turntable_east', 'hoist_used', 'vein_sorting_mined', 'vein_flooded_mined', 'vein_rim_mined',
                  'vein_se_mined', 'vein_sw_mined', 'vein_rich_mined']
for name in ('sorting', 'flooded', 'rim', 'se', 'sw', 'rich'):
    e = evt(f'evt:vein_{name}')
    e.pop('once', None)
    e['condition'] = {'not': {'map_var': f'vein_{name}_mined'}}
    e['sets'] = {'map_var': f'vein_{name}_mined'}
    e['else_effects'] = [{'text': 'Only bare rock is left where the seam was.'}]
evt('evt:vein_rich')['text'] = 'A fat seam of gold - and the rock beside it caves in!'

e = evt('evt:winch')
e.pop('once', None)
e['condition'] = {'not': {'qbit': 'x4_adit_open'}}
e['else_effects'] = [{'text': "The winch's rope hangs slack: the fall is gone."}]
e['text'] = 'The props come out and the whole fall slides away: daylight!'
evt('evt:exit_x4')['locked_text'] = 'Rock fills the adit to the roof. The winch might drag it away.'

e = evt('evt:brake')
e['title'] = 'Brake lever'
e.pop('once', None)
e.pop('locked_text', None)
e['condition'] = {'all': [{'not': {'qbit': 'deep_line_unchained'}}, {'item': 'brake_key', 'consume': True}]}
e['else_effects'] = [{'lua': (
    "if IsQBitSet(QBit(110021)) then evt.StatusText(\"The chain lies slack in the rail bed: the cart is free.\") "
    "else evt.SimpleMessage(\"The Deep Line cart is chained to this brake lever, the chain padlocked through it. "
    "The padlock wants a heavy iron key: the clan keeps it, with the tallymaster in his tally room off the "
    "mess hall.\") end")}]
e['text'] = 'The brake key opens the padlock: the chain falls away.'
e['notes'] = ("set:unchain_deep_cart: the brake key (consumed) frees the cart; the qbit opens the Deep Line exit. "
              "Before: a message window says where the key is; after: the chain lies slack.")
e = evt('evt:exit_deep')
e['locked_text'] = 'The Deep Line cart is chained to its brake lever.'
e['text'] = 'The cart runs down the Deep Line into the dark.'

# ---------------------------------------------------------------- lines that fit the status bar
evt('evt:points')['text'] = 'The turntable grinds round: the trestle line is live.'
evt('evt:points')['else_effects'][-1] = {'text': 'The turntable grinds round: the east line is live.'}
for eid in ('evt:trestle_car', 'evt:trestle_station', 'evt:trestle_turntable'):
    evt(eid)['locked_text'] = 'The points at the Turntable are set for the east line.'
for eid in ('evt:east_cart', 'evt:east_landing', 'evt:east_turntable'):
    evt(eid)['locked_text'] = 'The points at the Turntable are set for the trestle.'
evt('evt:web_wall')['text'] = 'You cut the web away; the rock screen behind it lifts.'
for eid in ('evt:hoist_floor', 'evt:hoist_rim'):
    evt(eid)['title'] = 'Hoist lever'
e = evt('evt:hoist_rim')
e.pop('locked_text', None)
e['else_effects'] = [{'message': "The bell rings far below; nobody answers. The cage waits on the stope floor, braked: "
                                 "ride it up once from the floor and its brake comes off."}]
evt('evt:hoist_floor')['locked_text'] = 'The cage is here: step in and work its lever.'

yio.save(L + 'rooms.yml', R)
yio.save(L + 'objects.yml', O)
yio.save(L + 'wiring.yml', W)
print('edited')
