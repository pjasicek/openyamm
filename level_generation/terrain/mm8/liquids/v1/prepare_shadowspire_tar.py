"""Choose a native Shadowspire tar pool outside expanded bmodel vertex bounds."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import json,subprocess,shutil,yaml
from common import *
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_odm_file
F=Path(__file__).resolve().parent
source=ROOT/'assets_dev/worlds/mm8/maps/out06.odm'
data=parse_odm_file(source)['payload'];grid=json.loads((P/'effective_grids.json').read_text())['out06']
spawns=[(s['position']['x'],s['position']['y']) for s in data['spawns']]
def position(y,x):return ((x+.5-64)*512,(64-y-.5)*512)
def distance(y,x):
    px,py=position(y,x)
    return min((px-sx)**2+(py-sy)**2 for sx,sy in spawns)**.5
boxes=[]
for model in data['bmodels']:
    vertices=np.asarray([[v['x'],v['y']] for v in model['vertices']])
    boxes.append((vertices.min(0)-128,vertices.max(0)+128))
candidates=[]
for y in range(12,115):
    for x in range(12,115):
        if grid[y][x]!='tartyl':continue
        point=np.asarray(position(y,x))
        if any(np.all(point>=a) and np.all(point<=b) for a,b in boxes):continue
        count=sum(n=='tartyl' for row in grid[y-2:y+3] for n in row[x-2:x+3])
        candidates.append((count,y,x))
_,y,x=max(candidates)
height=max(data['height_map'][yy*128+xx] for yy in (y,y+1) for xx in (x,x+1))*32
px,py=position(y,x);pose=[px,py,height+353,1.5707963268,-.6]
party=json.loads((ROOT/'level_generation/projects/brackenford_greywatch/source/baseline_party.json').read_text())
scenario=dict(id='mm8_shadowspire_tar_review',world='mm8',mode='faithful',steps=[
    dict(new_game_flow=dict(start_map='out06.odm',party=party)),
    dict(set_pose=dict(map='out06.odm',**dict(zip(['x','y','z','yaw','pitch'],pose)))),dict(save_game='seed')])
scenario_path=F/'shadowspire_tar_seed.yml';scenario_path.write_text(yaml.safe_dump(scenario,sort_keys=False))
with (F/'shadowspire_tar_seed.log').open('w') as log:
    subprocess.run([str(STAGE/'openyamm'),'--world','mm8','--headless-run-scenario',str(scenario_path),
                    '--scenario-no-color'],cwd=STAGE/'original',stdout=log,stderr=subprocess.STDOUT,check=True)
seed=F/'shadowspire_tar_seed.oysav';shutil.copy2('/tmp/openyamm_scenario_saves/mm8_shadowspire_tar_review/seed.oysav',seed)
save=F/'shadowspire_tar_flying.oysav'
subprocess.run(['/tmp/mm8-terrain-capture-save',str(seed),str(save),*map(str,pose),'--fly-buff'],check=True)
rpath=P/'reports/native_stage.json';report=json.loads(rpath.read_text());actions=F/'capture_cycle.json'
record=dict(map='out06',tile='tartyl',row=y,column=x,pose=pose,source_sha256=sha(source),
    nearest_spawn_distance=distance(y,x),start_save=str(save.relative_to(P)),start_save_sha256=sha(save),
    actions=str(actions.relative_to(P)),actions_sha256=sha(actions))
report['poses']['liquid_tar_pool']=record;rpath.write_text(json.dumps(report,indent=2)+'\n')
(F/'shadowspire_tar_pose.json').write_text(json.dumps(record,indent=2)+'\n')
print(record)
