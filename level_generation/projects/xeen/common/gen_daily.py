#!/usr/bin/env python3
"""A6 s25 (copy of s22/gen_daily.py for P1's Ember Font; D-70 Q2): writes devdocs/xeen/briefs/<map>/L4/playtest_daily.yml: each temporary
source used once (every member gains the amount), again the same day (the refusal line, no gain), then a day later
(the gain again). Event numbers from the map's ids.lock.yml.
Usage: gen_daily.py [map ...]"""
import os
import sys
import yaml

ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../..')
BRIEFS = os.path.join(ROOT, 'devdocs/xeen/briefs')
STATS7 = ['MightBonus', 'IntellectBonus', 'PersonalityBonus', 'EnduranceBonus', 'AccuracyBonus', 'SpeedBonus',
          'LuckBonus']
RES4 = ['FireResistanceBonus', 'AirResistanceBonus', 'WaterResistanceBonus', 'EarthResistanceBonus']
# (event key, title, kind, selectors and amount or None, gain text, refusal text)
SOURCES = {
    'p1': [('evt:font', 'The Ember Font', 'stats', (['FireResistanceBonus'], 20),
            '(+20 Fire resistance until you rest)', 'Nothing more happens.')],
}
EXT = {'p1': 'blv'}
MEMBERS = [{'name': 'Brokk', 'class': 'Knight'}, {'name': 'Hild', 'class': 'Cleric'},
           {'name': 'Ivar', 'class': 'Archer'}, {'name': 'Sefa', 'class': 'Sorcerer'}]
MANA = [1, 3]   # the members with spell points (Cleric, Sorcerer)


def readout(sels, slot):
    """Each member's value of every selector, kept under `slot` (the D5 hooks scenario's console read)."""
    lst = ', '.join(sels)
    return [{'console': {'line': "lua local out = '' for p = 0, 3 do evt.ForPlayer(p) for _, st in ipairs({%s}) do "
                                 "local v = 0 while v < 255 and IsAtLeast(st, v + 1) do v = v + 1 end out = out .. v "
                                 ".. '/' end out = out .. ' ' end evt.StatusText('stats ' .. out)" % lst,
                         'expect_contains': 'Lua ran.'}},
            {'play_lua': {'source': 'local s = string.match(status(), "stats ([%%d/ ]+)") if s == nil then '
                                    'error("no stats line") end remember("%s", s) log("%s: " .. s)' % (slot, slot)}}]


def compare(a, b, gain, sels, what):
    names = '{' + ', '.join('"%s"' % s for s in sels) + '}'
    src = ('local function parse(s) local m = {} for g in string.gmatch(s, "[%%d/]+") do local r = {} '
           'for v in string.gmatch(g, "%%d+") do r[#r + 1] = tonumber(v) end m[#m + 1] = r end return m end '
           'local a, b = parse(recall("%s")), parse(recall("%s")) local names = %s local bad = "" '
           'for m = 1, 4 do for k = 1, #names do if b[m][k] - a[m][k] ~= %d then bad = bad .. " member " .. (m - 1) '
           '.. " " .. names[k] .. " " .. a[m][k] .. "->" .. b[m][k] end end end '
           'if bad ~= "" then error("%s (want +%d):" .. bad) end log("%s: +%d for every member")'
           % (a, b, names, gain, what, gain, what, gain))
    return {'play_lua': {'source': src}}


def use(eid, text, note):
    """s32: A3's daily hooks answer on the status line since D-90 (touch effects): assert its text there."""
    return [{'note': note},
            {'execute_event': {'id': eid}},
            {'advance_runtime': {'seconds': 0.5}},
            {'play_lua': {'source': "local s = status(); if not string.find(s, %r, 1, true) then error('status: ' .. s) "
                                    "end" % text}},
            {'play_lua': {'source': 'close(); wait(0.3); close()'}}]


def low(kind):
    out = []
    for i in range(4):
        if kind == 'hp':
            out.append({'setup_shortcut': {'kind': 'set_member_points', 'member_index': i, 'health': 1}})
        elif i in MANA:
            out.append({'setup_shortcut': {'kind': 'set_member_points', 'member_index': i, 'spell_points': 0}})
    return out


def points(kind, restored):
    out = []
    for i in range(4):
        if kind == 'hp':
            out.append({'assert': {'member_points': {'member_index': i, 'health_min' if restored else 'health_max':
                                                     30 if restored else 1}}})
        elif i in MANA:
            out.append({'assert': {'member_points': {'member_index': i, 'spell_points_min' if restored else
                                                     'spell_points_max': 20 if restored else 0}}})
    return out


def scenario(m):
    ev = dict(yaml.safe_load(open(os.path.join(BRIEFS, m, 'L4/ids.lock.yml')))['events'])
    steps = [{'new_game_flow': {'start_map': 'xeen_%s.%s' % (m, EXT.get(m, 'odm')),
                                'party': {'gold': 200, 'food': 20,
                                          'members': [dict(x, level=10, skills=[], equipment={}) for x in MEMBERS]}}},
             {'setup_shortcut': {'kind': 'immortal'}},
             {'assert': {'map': 'xeen_%s.%s' % (m, EXT.get(m, 'odm'))}},
             {'advance_runtime': {'seconds': 4, 'present_dialogs': True}},
             {'play_lua': {'source': 'for _ = 1, 3 do if not close() then break end end'}},
             {'press_action': {'action': 'select_member', 'member_index': 0}}]
    for n, (key, title, kind, sel, gain, refusal) in enumerate(SOURCES[m]):
        eid = ev[key]
        tag = 's%d' % n
        if kind == 'stats':
            sels, amount = sel
            steps += readout(sels, tag + '_0')
            steps += use(eid, gain, '%s (event %d): every member +%d' % (title, eid, amount))
            steps += use(eid, refusal, '%s again the same day: the refusal line only' % title)
            steps += readout(sels, tag + '_1')
            steps.append(compare(tag + '_0', tag + '_1', amount, sels, title + ' today'))
            steps.append({'advance_game_time': {'hours': 24}})
            steps += use(eid, gain, '%s the next day: the gain again' % title)
            steps += use(eid, refusal, '%s again that day: refused' % title)
            steps += readout(sels, tag + '_2')
            steps.append(compare(tag + '_1', tag + '_2', amount, sels, title + ' the next day'))
        elif kind in ('hp', 'sp'):
            steps += low(kind)
            steps += use(eid, gain, '%s (event %d): every member restored' % (title, eid))
            steps += points(kind, True)
            steps += low(kind)
            steps += use(eid, refusal, '%s again the same day: the refusal line only' % title)
            steps += points(kind, False)
            steps.append({'advance_game_time': {'hours': 24}})
            steps += use(eid, gain, '%s the next day: restored again' % title)
            steps += points(kind, True)
        else:
            steps += use(eid, gain, '%s (event %d)' % (title, eid))
            steps += use(eid, refusal, '%s again the same day: refused' % title)
            steps.append({'advance_game_time': {'hours': 24}})
            steps += use(eid, gain, '%s the next day: again' % title)
            steps += use(eid, refusal, '%s again that day: refused' % title)
    doc = {'id': 'xeen.%s.playtest_daily' % m,
           'title': 'Xeen %s: temporary sources once a day for the party (D-70)' % m.upper(),
           'world': 'xeen', 'mode': 'faithful', 'tags': ['xeen', 'daily'], 'steps': steps}
    head = ('# Written by output/studio_cal/a6/s25/gen_daily.py (A6, D-70 Q2); do not edit by hand.\n'
            '# Each temporary source: once (every member gains), again the same day (refused, no gain), the next day '
            'again.\n')
    path = os.path.join(BRIEFS, m, 'L4/playtest_daily.yml')
    with open(path, 'w') as f:
        f.write(head + yaml.safe_dump(doc, sort_keys=False, width=200))
    print('wrote', path, len(steps), 'steps')


for m in sys.argv[1:] or sorted(SOURCES):
    scenario(m)
