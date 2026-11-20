"""Choose an isolated native Alvar lava pool, away from authored spawn points."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import json,subprocess,shutil,yaml
from common import *
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_odm_file
F=Path(__file__).resolve().parent
source=ROOT/'assets_dev/worlds/mm8/maps/out04.odm'
data=parse_odm_file(source)['payload'];grid=json.loads((P/'effective_grids.json').read_text())['out04']
spawns=[(s['position']['x'],s['position']['y']) for s in data['spawns']]
def position(y,x):return ((x+.5-64)*512,(64-y-.5)*512)
def distance(y,x):
    px,py=position(y,x)
    return min((px-sx)**2+(py-sy)**2 for sx,sy in spawns)**.5
candidates=[(y,x) for y in range(12,115) for x in range(12,115)
            if all(n=='lavtyl' for row in grid[y-2:y+3] for n in row[x-2:x+3])]
y,x=max(candidates,key=lambda p:distance(*p))
height=max(data['height_map'][yy*128+xx] for yy in (y,y+1) for xx in (x,x+1))*32
px,py=position(y,x);pose=[px,py,height+353,1.5707963268,-.6]
party=json.loads((ROOT/'level_generation/projects/brackenford_greywatch/source/baseline_party.json').read_text())
scenario=dict(id='mm8_alvar_lava_review',world='mm8',mode='faithful',steps=[
    dict(new_game_flow=dict(start_map='out04.odm',party=party)),
    dict(set_pose=dict(map='out04.odm',**dict(zip(['x','y','z','yaw','pitch'],pose)))),dict(save_game='seed')])
scenario_path=F/'alvar_lava_seed.yml';scenario_path.write_text(yaml.safe_dump(scenario,sort_keys=False))
with (F/'alvar_lava_seed.log').open('w') as log:
    subprocess.run([str(STAGE/'openyamm'),'--world','mm8','--headless-run-scenario',str(scenario_path),
                    '--scenario-no-color'],cwd=STAGE/'original',stdout=log,stderr=subprocess.STDOUT,check=True)
seed=F/'alvar_lava_seed.oysav';shutil.copy2('/tmp/openyamm_scenario_saves/mm8_alvar_lava_review/seed.oysav',seed)
save=F/'alvar_lava_flying.oysav'
subprocess.run(['/tmp/mm8-terrain-capture-save',str(seed),str(save),*map(str,pose),'--fly-buff'],check=True)
rpath=P/'reports/native_stage.json';report=json.loads(rpath.read_text());actions=F/'capture_cycle.json'
record=dict(map='out04',tile='lavtyl',row=y,column=x,pose=pose,source_sha256=sha(source),
    nearest_spawn_distance=distance(y,x),start_save=str(save.relative_to(P)),start_save_sha256=sha(save),
    actions=str(actions.relative_to(P)),actions_sha256=sha(actions))
report['poses']['liquid_lava_alvar']=record;rpath.write_text(json.dumps(report,indent=2)+'\n')
(F/'alvar_lava_pose.json').write_text(json.dumps(record,indent=2)+'\n')
print(record)
