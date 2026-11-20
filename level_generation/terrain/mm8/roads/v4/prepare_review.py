"""Prepare independent native-map stages for the road-edge regression review."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from common import *
import json
import configparser
import shutil
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_odm_file

stage = STAGE / 'road_edges_v4'
assets = stage / 'assets_dev'
for relative in ('', 'worlds', 'worlds/mm8'):
    dst = assets / relative; dst.mkdir(parents=True, exist_ok=True)
    for source in (ROOT / 'assets_dev' / relative).iterdir():
        target = dst / source.name
        if source.name in ({'worlds'} if relative == '' else {'mm8'} if relative == 'worlds' else {'terrain_x2'}):
            continue
        if not target.exists(): target.symlink_to(source, target_is_directory=source.is_dir())
textures = assets / 'worlds/mm8/terrain_x2'; textures.mkdir(exist_ok=True)
for source in (P / 'complete_runtime_x2/worlds/mm8/terrain_x2').glob('*.png'):
    replacement = HERE / 'runtime' / source.name
    shutil.copy2(replacement if replacement.exists() else source, textures / source.name)
config = configparser.ConfigParser(interpolation=None)
config.read(STAGE / 'enhanced/settings.ini')
config['assets']['root'] = str(assets)
config['video_quality']['terrain'] = 'x2'
with (stage / 'settings.ini').open('w') as stream: config.write(stream)
grid = json.loads((P / 'effective_grids.json').read_text())
inv = json.loads((P / 'inventory.json').read_text())
poses = {}
for map_id in ('out01','out03'):
    data = parse_odm_file(ROOT / next(r['source'] for r in inv['maps'] if r['id']==map_id))['payload']
    g = grid[map_id]
    def run(pos):
        y,x=pos
        return sum(g[yy][x]=='drsrns' for yy in range(max(0,y-3),min(127,y+4)))
    y,x = max(((y,x) for y in range(8,119) for x in range(8,119) if g[y][x]=='drsrns'),key=run)
    h=max(data['height_map'][yy*128+xx] for yy in (y,y+1) for xx in (x,x+1))*32
    poses[map_id]=[(x+.5-64)*512,(64-y-.5)*512,h+161,1.5707963268,-.22]
report = dict(stage=str(stage), files={f.name:sha(f) for f in textures.glob('*.png')}, poses=poses)
(HERE / 'review_stage.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(poses))
