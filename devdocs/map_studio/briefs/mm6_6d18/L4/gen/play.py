#!/usr/bin/env python3
# Writes the playtest of the Gharik's Forge rebuild (L4/playtest.yml) from a list of waypoints and actions.
import sys, yaml
L4 = '/home/pjasicek/github/OpenYAMM/devdocs/map_studio/briefs/mm6_6d18/L4/'
ids = yaml.safe_load(open(L4 + 'ids.lock.yml'))
EV = ids['events']
DR = ids['doors']
steps = [{'new_game_flow': {'start_map': 'cal6d18.blv'}}, {'assert': {'map': 'cal6d18.blv'}},
         {'setup_shortcut': {'kind': 'immortal', 'value': True}}]


def w(x, y, z, r=56, t=60):
    steps.append({'walk_to': {'x': x, 'y': y, 'z': z, 'radius': r, 'timeout_seconds': t, 'clear_hostiles': 2500}})


def at(x, y, zlo, zhi, r=90):
    steps.append({'play_lua': {'source': 'wait(1)'}})
    steps.append({'assert': {'party_position': {'x': x, 'y': y, 'radius': r, 'z_min': zlo, 'z_max': zhi}}})


def lua(src):
    steps.append({'play_lua': {'source': src}})


def click(evt, wait=2):
    lua('click(%d); wait(%s)' % (EV[evt], wait))


def opened(door, evt, wait=3):
    lua('if door_state(%d) ~= "closed" then error("%s does not start shut: " .. door_state(%d)) end\nclick(%d); wait(%s)\n'
        'if door_state(%d) ~= "open" then error("%s did not open: " .. door_state(%d)) end'
        % (DR[door], door, DR[door], EV[evt], wait, DR[door], door, DR[door]))


def pose(x, y, z, yaw=0):
    steps.append({'set_pose': {'map': 'cal6d18.blv', 'x': x, 'y': y, 'z': z, 'yaw_degrees': yaw, 'pitch': 0}})


SEG = sys.argv[1:] or ['all']


def seg(name):
    return 'all' in SEG or name in SEG


if seg('tower'):
    # the bridge, then twice round the tower down the ramp
    w(-2688, 900, 1152); w(-2688, 640, 1152); w(-2300, 640, 1152); w(-700, 640, 1152); w(-550, 600, 1152)
    w(-550, -330, 1024); at(-550, -330, 1010, 1070)
    w(-707, -445, 1024); w(-850, -573, 1024); w(-1840, -573, 896); w(-1981, -445, 896)
    w(-2109, -330, 896); w(-2109, 1600, 768); w(-1981, 1725, 768); w(-1850, 1853, 768)
    w(-840, 1853, 640); w(-707, 1725, 640); w(-617, 1570, 640); w(-617, -250, 512)
    w(-707, -445, 512); w(-920, -573, 512); w(-1770, -573, 384); w(-1981, -445, 384)
    w(-2109, -250, 384); w(-2109, 1530, 256); w(-1981, 1725, 256); w(-1770, 1853, 256)
    w(-920, 1853, 128); w(-707, 1725, 128); w(-550, 1550, 128); w(-550, 800, 0)
    w(-576, 640, 0); at(-576, 640, -4, 8)
    w(-300, 640, 0); w(128, 640, 0); w(128, 1100, 0); w(128, 1664, 0)
if seg('hall'):
    if not seg('tower'):
        pose(128, 1664, 0)
    # the split door, the lever, the bridge over the first lava hall
    w(400, 1664, 0)
    opened('door:d1', 'evt:door1')
    w(800, 1664, 0); w(1150, 1664, 0); w(1280, 1000, 0); w(1480, 850, 0)
    lua('click(%d); wait(6)\nif door_state(%d) ~= "open" then error("the bridge did not rise") end' % (EV['evt:lever3'], DR['lift:bridge3']))
    w(1280, 1000, 0); w(1150, 1664, 0); w(128, 1664, 0); w(128, 2000, 0)
    w(128, 2090, -16); w(128, 2600, -16); at(128, 2600, -24, -8)
    w(128, 3040, -16); w(128, 3200, 0); w(128, 3968, 0); w(-1600, 3968, 0); w(-1740, 4040, 0)
    opened('door:d6', 'evt:lever4')
    w(-1792, 4040, 0); w(-1792, 4300, 0); at(-1792, 4300, -4, 4)
    w(-1792, 5248, 0); w(-1600, 5270, 0)
    opened('door:d10', 'evt:lever6')
    w(-1300, 5248, 0); w(-896, 5248, 0); w(-896, 4992, 0); w(640, 4992, 0); w(640, 4736, 0); w(1920, 4736, 0)
if seg('machine'):
    if not seg('hall'):
        pose(1920, 4736, 0, 90)
    w(1920, 5000, 0); w(1920, 5248, 0); w(1920, 5888, 0); at(1920, 5888, -4, 4); w(1920, 6500, 0)
    w(1860, 6800, 0)
    opened('door:gate51', 'evt:lever36')
    w(1920, 7040, 0); w(1920, 7296, 0); w(1024, 7296, 0); w(1024, 6700, -260); w(1024, 6016, -260)
    at(1024, 6016, -264, -256)
    w(700, 6016, -400); w(384, 6016, -512); w(384, 7296, -512); w(2208, 7296, -512); w(2208, 7040, -512)
    w(2208, 6800, -512); w(2290, 6850, -512)
    opened('door:gate49', 'evt:lever40')
    w(2208, 7040, -512); w(2208, 7296, -512); w(2912, 7296, -512); w(2912, 7040, -512); w(2912, 6800, -512)
    w(2830, 6850, -512)
    opened('door:gate52', 'evt:lever39')
    w(2912, 7040, -512); w(2912, 7296, -512); w(384, 7296, -512); w(384, 4476, -512, t=120); w(2912, 4476, -512, t=120)
    w(2912, 4800, -512); w(2912, 5200, -512); w(2830, 5190, -512)
    lua('click(%d); wait(6)\nif door_state(%d) ~= "open" then error("the east bridge did not rise") end\n'
        'if door_state(%d) ~= "closed" then error("the west bridge did not sink") end'
        % (EV['evt:lever8'], DR['lift:bridge_e'], DR['lift:bridge_w']))
    w(2912, 4800, -512); w(2912, 4476, -512); w(384, 4476, -512, t=120); w(384, 6016, -512); w(700, 6016, -400)
    w(1024, 6016, -260); w(1024, 5200, -260); w(1024, 4736, 0); w(3200, 4736, 0, t=120); w(3200, 5000, 0)
    w(3200, 5248, 0); w(3200, 5888, 0); at(3200, 5888, -4, 4); w(3200, 6656, 0); w(3200, 7050, 0); w(3200, 7400, 0)
if seg('ring'):
    if not seg('machine'):
        pose(3200, 7400, 0, 90)
    w(3200, 7808, 0); w(4992, 7808, 0, t=120); w(4992, 5800, 0, t=120); w(4930, 5740, 0)
    opened('door:d18', 'evt:lever10')
    w(4992, 5740, 0); w(4992, 5400, 0); w(4500, 4760, 0); w(4430, 4800, 0)
    opened('door:d20', 'evt:lever11')
    w(4430, 4736, 0); w(4200, 4736, 0); w(3968, 4736, 0); w(3968, 3456, 0, t=120); w(4040, 3400, 0)
    opened('door:d22', 'evt:lever12')
    w(4040, 3456, 0); w(4300, 3456, 0); w(4736, 3456, 0); w(4736, 2700, 0); w(4680, 2660, 0)
    opened('door:d26', 'evt:lever14')
    w(4736, 2660, 0); w(4736, 2440, -16); at(4736, 2440, -24, -8)
    # the lift: ten seconds down
    lua('click(%d); wait(13)\nif door_state(%d) ~= "closed" then error("the lift did not go down: " .. door_state(%d)) end'
        % (EV['evt:lever15_top'], DR['lift:shaft'], DR['lift:shaft']))
    at(4736, 2440, -2050, -2030)
if seg('lower'):
    if not seg('ring'):
        pose(4736, 2200, -2048, -90)
    w(4736, 2200, -2048); w(4690, 2130, -2048)
    lua('click(%d); wait(2)\nif door_state(%d) ~= "closed" then error("the laboratory door opened without the key") end'
        % (EV['evt:lever16'], DR['door:d30']))
    steps.append({'grant_item': {'item_id': 2107, 'member_index': 0}})
    opened('door:d30', 'evt:lever16')
    w(4736, 2130, -2048); w(4736, 1408, -2048); w(6016, 1408, -2048); w(6016, 1150, -2048); w(5960, 1110, -2048)
    opened('door:d32', 'evt:lever17')
    w(6016, 1110, -2048); w(6016, 900, -2048); w(5700, 640, -2048); w(5200, 640, -1952); w(4736, 640, -1952)
    at(4736, 640, -1956, -1948)
    w(4200, 640, -1990); w(3700, 640, -2048); w(3450, -128, -2048); w(3390, -80, -2048)
    opened('door:d34', 'evt:lever18')
    w(3390, -128, -2048); w(3000, -128, -2048); w(2300, -128, -2048); w(2270, -80, -2048)
    opened('door:d36', 'evt:lever19')
    w(2270, -128, -2048); w(2000, -128, -2048)
    # three times round the stair tower
    w(1900, 400, -2048); w(1900, 573, -2048); w(700, 573, -1920); w(579, 573, -1920)
    w(579, -500, -1856); w(579, -573, -1856); w(2000, -573, -1728); w(2109, -573, -1728)
    w(2109, 500, -1664); w(2109, 573, -1664); w(660, 573, -1536); w(579, 590, -1536)
    w(579, -520, -1472); w(579, -590, -1472); w(2040, -590, -1344); w(2109, -590, -1344)
    w(2109, 520, -1280); w(2109, 590, -1280); w(640, 590, -1152); w(565, 600, -1152)
    w(565, -540, -1088); w(565, -600, -1088); w(2060, -600, -960); w(2120, -600, -960)
    w(2120, 600, -896); at(2120, 600, -900, -890)
    w(2110, 615, -896)
    opened('door:d38', 'evt:lever20')
    w(2048, 615, -896); w(2048, 800, -896); w(2048, 1150, -896); w(2944, 1150, -896); w(2944, 1344, -896)
    w(2944, 2000, -896); at(2944, 2000, -900, -892)
    w(2944, 2800, -896); w(3300, 2944, -896); w(5000, 2944, -896, t=120); w(5040, 2890, -896)
    opened('door:d40', 'evt:lever21')
    w(5040, 2944, -896); w(5400, 2944, -896); w(6500, 2864, -896)
    lua('loot_chest(%d)\nif not qbit(1029) then error("the hourglass chest did not set its quest bit") end\nif not has_item(2053) then error("no Hourglass of Time in the chest") end' % EV['evt:chest5'])

yaml.safe_dump({'id': 'studio.cal6d18.walk', 'title': "Gharik's Forge rebuild, the critical path and every mechanism on it",
                'world': 'mm6', 'mode': 'faithful', 'steps': steps}, open(L4 + 'playtest.yml', 'w'), sort_keys=False, width=200)
print(len(steps), 'steps')
