import runpy,sys,bpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
def run(n,args):
 sys.argv=[n,'--']+[str(x) for x in args];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('transfer_uv.py',[p/'work/rig_v9h.blend',p/'meshy/retexture_v1',p/'work/rig_v9.blend'])
run('transfer_uv.py',[p/'work/rig_v9.blend',p/'meshy/head_retexture_v1',p/'work/rig_v9.blend','HeadUV'])
for uv in ['UVMap','HeadUV']:run('uv_raster.py',[p/'work/rig_v9.blend',uv,1024])
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v9.blend'))
bpy.data.objects['Body'].data.uv_layers.active=bpy.data.objects['Body'].data.uv_layers['UVMap']
import numpy as np,json
r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];a=bpy.data.actions['Walking'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
heights=[]
for f in range(25):
 bpy.context.scene.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 co=np.array([tuple(v.co) for v in me.vertices]);heights.append(float(co[:,2].max()-co[:,2].min()));ev.to_mesh_clear()
scale=269*.699997/max(heights)
(p/'work/runtime_scale.json').write_text(json.dumps({'native_height':269*.699997,'walk_height_m':max(heights),'scale':scale,'walk_heights':heights},indent=1))
print('RUNTIME_SCALE',scale,'height',max(heights))
sys.argv=['ao','--','Body',str(p/'work/ao_body.png'),'.03','1024']
runpy.run_path(str(p.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
