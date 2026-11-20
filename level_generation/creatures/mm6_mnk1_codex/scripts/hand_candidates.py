import bpy,runpy,sys,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
runpy.run_path(str(p/'scripts/build_rig.py'),run_name='__main__')
sys.argv=['finger_candidates.py','--',str(p/'work/rig_v1.blend')]
runpy.run_path(str(p/'scripts/finger_candidates.py'),run_name='__main__')
body=bpy.data.objects['Body'];me=body.data;me.materials.clear()
cols=[(.6,.6,.6,1),(.9,.1,.1,1),(.1,.7,.1,1),(.1,.3,.9,1),(.9,.7,.1,1),(.8,.1,.8,1),(.1,.8,.8,1),(.8,.4,.1,1)]
for c in cols:
 m=bpy.data.materials.new('label');m.diffuse_color=c;me.materials.append(m)
for sd,x in [('R',-.52),('L',.51)]:
 labels=json.loads((p/'work'/f'finger_candidates_{sd}.json').read_text());mapping={int(v):i+1 for i,vs in enumerate(labels.values()) for v in vs}
 for f in me.polygons:f.material_index=mapping.get(f.vertices[0],0)
 common.workbench_clay(bpy.context.scene);common.render_views(str(p/'review'/f'finger_candidates_{sd}'),.99,.32,views=('front','back'),resolution=(800,800),target=(x,-.10))
