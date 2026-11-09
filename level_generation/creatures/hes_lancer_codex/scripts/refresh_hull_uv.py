"""Keep the retained graft/equipment islands inside the rebuilt ceramic atlas."""
import bpy,json,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=src)
old=json.loads((P/'work/review_before_20261023/armour_layout.json').read_text())
new=json.loads((P/'work/armour_layout.json').read_text());dest=new['plates']['back']['rect']
for o in bpy.data.objects:
    if o.type!='MESH' or not (o.name=='Ancient_Graft' or o.name=='Thunder_Maul' or o.name.startswith('Apron_')):continue
    rect=o.get('lancer_atlas_rect',old['plates']['chest']['rect']);atlas=o.get('lancer_atlas_size',old['atlas'])
    for loop in o.data.uv_layers.active.data:
        u=(loop.uv.x*atlas-rect[0])/rect[2];v=((1-loop.uv.y)*atlas-rect[1])/rect[3]
        assert -.001<=u<=1.001 and -.001<=v<=1.001,(o.name,u,v)
        loop.uv=((dest[0]+u*dest[2])/new['atlas'],1-(dest[1]+v*dest[3])/new['atlas'])
    o['lancer_atlas_rect']=dest;o['lancer_atlas_size']=new['atlas']
bpy.ops.wm.save_as_mainfile(filepath=out)
