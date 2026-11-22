# families.py <L4>: each project texture with the family maps that use it (6d05, 6d09, 7d34) or else its main map.
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../openyamm-studio/calibration'))
import texture_use
idx, names = texture_use.load()
found = texture_use.project_textures(sys.argv[1])
fam = {'mm6/6d05.blv': '6d05', 'mm6/6d09.blv': '6d09', 'mm7/7d34.blv': '7d34'}
for t in sorted(found):
    maps = idx.get(t, {})
    hit = [f'{fam[k]} {maps[k]}' for k in fam if k in maps]
    if hit:
        print(f'{t:12s} family: {", ".join(hit)}  (in {len(maps)} dungeons)')
    elif maps:
        top = max(maps.items(), key=lambda kv: kv[1])
        print(f'{t:12s} OUTSIDE: {top[0]} {names.get(top[0].split("/")[1], "?")} {top[1]}  (in {len(maps)} dungeons)')
    else:
        print(f'{t:12s} NO SHIPPED DUNGEON')
