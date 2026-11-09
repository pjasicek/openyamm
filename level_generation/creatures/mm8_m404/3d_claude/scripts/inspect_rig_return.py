import runpy,sys,bpy,bmesh,numpy as np,json
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.argv=['meshy_joints.py','--',str(p.parent/'meshy/body_rig_v2/result_rigged_character_glb_url.glb'),str(p/'work/step1.blend')]
runpy.run_path(str(p/'scripts/meshy_joints.py'),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(p/'work/assembled_parts.blend'))
out={}
for side,name in [('R','P03'),('L','P04')]:
 o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data)
 ring=list({v for e in bm.edges if e.is_boundary for v in e.verts});co=np.array([v.co[:] for v in ring]);out[side]=co.mean(0).tolist();print('WRIST_BOUNDARY',side,out[side],len(ring),co.min(0),co.max(0));bm.free()
json.dump(out,open(p/'work/wrist_rings.json','w'),indent=2)
