#!/usr/bin/env python3
"""X4 (A5, 21st session): playtest_daily.yml, D-70 Q2's check on the quintain. Every member gets +5 Accuracy from the
first tilt of the day; a second tilt the same day gives the refusal line and no more (+5, not +10); a rest clears the
bonus and the quintain still refuses that day; the next day it gives +5 again.
  python3 level_generation/projects/xeen/x4/gen_daily.py devdocs/xeen/briefs/x4/L4 output/studio_cal/x4/build_w"""
import json
import math
import os
import subprocess
import sys

import yaml

P, B = sys.argv[1], sys.argv[2]
M = 'xeen_x4.odm'
exp_path = os.path.join(B, 'export_daily.json')
subprocess.run(['openyamm-studio/build-xeen/oymap', 'export', os.path.join(B, M), '--out', exp_path], check=True,
               stdout=subprocess.DEVNULL)
hm = json.load(open(exp_path))['map']['terrain']['height_map']
os.remove(exp_path)
ev = dict(yaml.safe_load(open(os.path.join(P, 'ids.lock.yml')))['events'])
QUINTAIN = ev['evt:thing:quintain']


def W(x, y):
    return (round((x - 64) * 512), round((64 - y) * 512))


def ground(X, Y):
    x, y = X / 512.0 + 64, 64 - Y / 512.0
    i, j = int(math.floor(x)), int(math.floor(y))
    fx, fy = x - i, y - j

    def h(a, b):
        return hm[max(0, min(127, b)) * 128 + max(0, min(127, a))] * 32
    return round(h(i, j) * (1 - fx) * (1 - fy) + h(i + 1, j) * fx * (1 - fy) + h(i, j + 1) * (1 - fx) * fy
                 + h(i + 1, j + 1) * fx * fy)


READ = {'console': {'line': ("lua local out = '' for p = 0, 3 do evt.ForPlayer(p) local v = 0 while v < 255 and "
                             "IsAtLeast(AccuracyBonus, v + 1) do v = v + 1 end out = out .. v .. '/' end "
                             "evt.ForPlayer(Players.Current) evt.StatusText('ab ' .. out)"),
                    'expect_contains': 'Lua ran.'}}


def check(delta, label):
    """Every member's Accuracy bonus is `delta` above the one remembered before the first tilt."""
    return [READ, {'play_lua': {'source': (
        "local now = {} for v in string.gmatch(string.match(status(), 'ab ([%d/]+)'), '%d+') do "
        "table.insert(now, tonumber(v)) end local was = {} for v in string.gmatch(recall('ab'), '%d+') do "
        "table.insert(was, tonumber(v)) end "
        f"log('{label}: Accuracy bonus ' .. table.concat(now, '/')) for i = 1, 4 do "
        f"if now[i] - was[i] ~= {delta} then error('{label}: member ' .. (i - 1) .. ' has ' .. (now[i] - was[i]) .. "
        f"', wanted {delta}') end end")}}]


def tilt(contains):
    return [{'play_lua': {'source': f'click({QUINTAIN}); wait(0.5)'}},
            {'play_lua': {'source': "local s = status(); if not string.find(s, %r, 1, true) then "
                                    "error('no status line: ' .. s) end" % contains}}]   # F13 (A5 s29)


GAIN = '(+5 Accuracy until you rest)'
AGAIN = 'Enough tilting for one day.'
X, Y = W(60.5, 94.2)
steps = [
    {'new_game_flow': {'start_map': M, 'party': {'gold': 0, 'food': 20, 'members': [
        {'name': 'Brokk', 'class': 'Knight', 'level': 10, 'skills': [], 'equipment': {}},
        {'name': 'Hild', 'class': 'Cleric', 'level': 10, 'skills': [], 'equipment': {}},
        {'name': 'Ivar', 'class': 'Archer', 'level': 10, 'skills': [], 'equipment': {}},
        {'name': 'Sefa', 'class': 'Sorcerer', 'level': 10, 'skills': [], 'equipment': {}}]}}},
    {'setup_shortcut': {'kind': 'immortal', 'value': True}},
    {'play_lua': {'source': 'wait(3); for _ = 1, 3 do if not close() then break end end'}},
    {'assert': {'map': M}},
    {'note': 'Beside the quintain on its field south of Burlock (60.5, 93.5).'},
    {'set_pose': {'map': M, 'x': X, 'y': Y, 'z': ground(X, Y) + 32, 'yaw': 1.5708, 'pitch': 0.0}},
    {'advance_runtime': {'seconds': 1.0}},
    {'play_lua': {'source': "log('cleared ' .. clear_hostiles(9000))"}},
    READ,
    {'play_lua': {'source': "local s = string.match(status(), 'ab ([%d/]+)'); remember('ab', s); "
                            "log('Accuracy bonus before: ' .. s)"}},
    {'note': 'Two tilts the same day: +5 for every member, not +10.'}]
steps += tilt(GAIN) + tilt(AGAIN) + check(5, 'after two tilts')
steps += [{'note': 'A rest clears the bonus; the quintain still refuses the same day.'},
          # the whole map's foes (a rest is refused while one is near; 9,000 was not enough on the savannah)
          {'play_lua': {'source': "log('cleared ' .. clear_hostiles(40000)); wait(2); log('cleared ' .. "
                                  "clear_hostiles(40000))"}},
          {'console': {'line': 'rest heal 480', 'expect_contains': 'Resting'}},
          {'advance_runtime': {'seconds': 20}},
          {'console': {'line': 'rest close'}}]
steps += check(0, 'after the rest') + tilt(AGAIN) + check(0, 'after a tilt the same day')
steps += [{'note': 'The next day: +5 again.'}, {'advance_game_time': {'hours': 24}},
          {'play_lua': {'source': "log('cleared ' .. clear_hostiles(9000))"}}]
steps += tilt(GAIN) + check(5, 'the next day')
doc = {'id': 'xeen.x4.daily', 'title': "Burlock (X4): the quintain once a day for the party (D-70): +5 every member, "
       'not +10; gone after a rest; +5 again the next day', 'world': 'xeen', 'mode': 'faithful', 'steps': steps}
with open(os.path.join(P, 'playtest_daily.yml'), 'w') as f:
    f.write("# D-70 Q2 on X4's quintain (written by output/studio_cal/x4/tools/gen_daily.py): two tilts give every\n"
            "# member +5 Accuracy, not +10; a rest clears it and the quintain refuses the rest of the day; the next\n"
            "# day it gives +5 again.\n")
    yaml.safe_dump(doc, f, sort_keys=False, width=120, allow_unicode=True)
print('written', os.path.join(P, 'playtest_daily.yml'), 'quintain event', QUINTAIN)
