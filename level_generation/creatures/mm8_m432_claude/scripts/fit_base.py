import bpy,json,sys,runpy,math
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/body_clean.blend'))
o=bpy.data.objects['Body']; changed=[]
for v,orig,piece in zip(o.data.vertices,o.data.attributes['orig_co'].data,o.data.attributes['piece'].data):
    v.co=orig.vector
    x,y,z=v.co
    if piece.value!=1: continue
    # Pull only the upper outer ear rim; the lobe and facial silhouette stay fixed.
    upper=max(0,1-abs(z-1.777)/.034)
    outer=max(0,min(1,(abs(x)-.076)/.017))
    depth=max(0,1-abs(y-.006)/.024)
    w=upper*outer*depth
    if w:
        v.co.x+=math.copysign(.036*w,x);v.co.y+=.014*w;v.co.z+=.032*w
        changed.append(v.index)
assert len(changed)>15
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/body_clean.blend'))
common.workbench_clay(bpy.context.scene)
common.render_views(str(P/'review/ear_repair'),1.76,.34,views=('front','left','right','three_quarter'),resolution=(700,700))
(P/'work/ear_repair.json').write_text(json.dumps({'vertices':changed,'orig_co_preserved':True},indent=1))
sys.argv=['meshy_joints.py','--',str(P/'meshy/rig_v1/result_rigged_character_glb_url.glb'),str(P/'work/body_clean.blend')]
runpy.run_path(str(P/'scripts/meshy_joints.py'),run_name='__main__')
m=json.loads((P/'work/meshy_joints.json').read_text());m['height_m']=1.9
(P/'work/meshy_joints.json').write_text(json.dumps(m,indent=1))
sys.argv=['joint_xray.py','--',str(P/'work/body_clean.blend'),'Body',str(P/'work/meshy_joints.json'),str(P/'review/joints_meshy'),str(P/'work/joints.json')]
runpy.run_path(str(P/'scripts/joint_xray.py'),run_name='__main__')
