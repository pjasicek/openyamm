import pathlib
"""A7, D-7: dressing moves on XD-01, XD-02, XD-04, XD-05 (props off the walking lines and against walls)."""
B = str(pathlib.Path(__file__).resolve().parents[5]) + '/devdocs/xeen/briefs/'
def move(key, ident, old, new, f='objects.yml'):
    p = B + key + '/L4/' + f
    s = open(p).read()
    a = s.index(f'  - id: {ident}\n')
    i = s.index(f'at: {old}', a)
    assert i - a < 300, (key, ident)
    s = s[:i] + f'at: {new}' + s[i + len(f'at: {old}'):]
    open(p, 'w').write(s)
# XD-01: the loading bay's pallet and its sacks by the south-east corner, out of the cart way; the bottle beside it.
move('xd01', 'deco:bay_pallet_sacks_1', '[960, 680]', '[1555, 165]')
move('xd01', 'deco:bay_pallet_sacks_2', '[1045, 735]', '[1645, 225]')
move('xd01', 'item:bay_bottle', '[1700, 160]', '[1740, 330]')
# XD-01: the feed store's pallet against its west wall (the store is a storeroom, store: true once the audit reads it).
move('xd01', 'deco:feed_sacks_4', '[100, 5300]', '[-240, 5260]')
move('xd01', 'deco:feed_sacks_7', '[220, 5300]', '[-120, 5340]')
# XD-01: the cistern's feeding station off the line from the west arch to the east doorway.
move('xd01', 'deco:pens_mash', '[1896, 5572]', '[1896, 5628]')
move('xd01', 'deco:pens_bucket', '[1956, 5512]', '[1972, 5584]')
# XD-02: the top station's bucket off the line to the trestle.
move('xd02', 'deco:top_station_19', '[12262, 5032]', '[12272, 5052]')
# XD-04: the dormitory bucket off the line between its doors.
move('xd04', 'deco:dorm_bucket', '[2985, 904]', '[2930, 916]')
# XD-05: the keg stood on a stalactite's top: on the floor by the south wall, a pair with the cask.
move('xd05', 'deco:cook_keg', '[-1050, 6200]', '[-730, 5850]')
# The rooms.yml platforms of XD-01 (the two pallets).
p = B + 'xd01/L4/rooms.yml'
s = open(p).read()
old = '{at: [1000, 700], size: [192, 160], rise: 16, surface: {texture: t66floor, size: [128, 128]}, top_surface: {texture: t66floor, size: [128, 128]}, notes: "A pallet of sacks waiting to go in, in the middle of the bay with room all round."}'
assert old in s
s = s.replace(old, '{at: [1600, 190], size: [192, 160], rise: 16, surface: {texture: t66floor, size: [128, 128]}, top_surface: {texture: t66floor, size: [128, 128]}, notes: "A pallet of sacks waiting to go in, in the south-east corner, out of the cart way (D-7, 2026-11-20)."}')
old = '{at: [160, 5320], size: [256, 192], rise: 16,'
assert old in s
s = s.replace(old, '{at: [-176, 5300], size: [256, 192], rise: 16,')
s = s.replace('the cart way from the ramp to the barn doors runs clear down the middle past a pallet of sacks.', 'the cart way from the ramp to the barn doors runs clear down the middle; a pallet of sacks waits in the south-east corner.')
open(p, 'w').write(s)
print('ok')
