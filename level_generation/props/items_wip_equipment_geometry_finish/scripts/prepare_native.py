"""Bounded native reviews of the six accepted entries; duplicate boots use the same canonical export."""
import json,sys
from pathlib import Path
import yaml
P=Path(__file__).resolve().parents[1];R=P.parents[2]
owned={x['icon']:x for x in json.loads((P/'ownership.json').read_text())}
positions=json.loads((P/'receipts/settled_positions.json').read_text())['positions']
icons=['6boots1','6boots5','6boots6','6boots7','7item348','7item096']
def write(name,shots):
    (P/f'review/{name}_tour.yml').write_text(yaml.safe_dump({'output_dir':str((P/f'review/native_{name}').resolve()),'settle_seconds':1.5,'exit':True,'shots':shots},sort_keys=False))
shots=[]
for icon in icons:
    x,y,z=positions[icon]
    shots.extend([{'name':icon+'-normal','position':[x,y+280,z+20],'yaw':-1.5707963,'pitch':-.58,'time':'12:00'},
                  {'name':icon+'-low','position':[x-150,y+170,z-75],'yaw':-.785398,'pitch':-.30}])
write('outdoor',shots)
sys.path.insert(0,str(R/'tools'))
from export_indoor_scene_yml import parse_indoor_blv
scene=parse_indoor_blv(R/'assets_dev/worlds/mm6/maps/6d19.blv')
assert {scene['vertices'][i]['z'] for i in scene['face_vertex_ids'][12]}=={0}
shots=[]
for icon in ['6boots1','6boots5','7item348','7item096']:
    canonical='6boots5' if icon in ['6boots6','6boots7'] else icon
    low,high=json.loads((P/f'review/equipment_{canonical}_export_check.json').read_text())['bounds_gltf']
    scale=owned[icon]['length']/max(high[0]-low[0],high[2]-low[2])
    shots.extend([{'name':icon+'-dim','position':[0,-1690,0],'yaw':1.5707963,'pitch':-.52,'commands':['model stop all',f"model spawn {owned[icon]['model']} 0 -1400 1 {scale} 0"],'settle_seconds':2},
                  {'name':icon+'-dim-low','position':[0,-1770,-60],'yaw':1.5707963,'pitch':-.30}])
write('indoor',shots)
