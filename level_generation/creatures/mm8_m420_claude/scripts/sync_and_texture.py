"""Carry the final motion into the already-uploaded UV master, retaining exact body geometry."""
import bpy,sys,runpy,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work';sys.path.insert(0,str(P/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(W/'master_uv_upload.blend'));body=bpy.data.objects['Body'];oldrig=bpy.data.objects['Rig'];rest={b.name:b.matrix_local.copy() for b in oldrig.data.bones if b.name not in ['Staff','Socket_Staff']}
world=body.matrix_world.copy();body.parent=None;body.matrix_world=world
for name in ['Rig','StaffMesh']:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
with bpy.data.libraries.load(str(W/'equipped.blend'),link=False) as (src,dst):
 dst.objects=['Rig','StaffMesh'];dst.actions=list(src.actions)
for o in dst.objects:bpy.context.collection.objects.link(o)
rig=next(o for o in dst.objects if o.type=='ARMATURE');rig.name='Rig'
for n,m in rest.items():assert np.max(abs(np.array(m)-np.array(rig.data.bones[n].matrix_local)))<1e-6,n
for mod in body.modifiers:
 if mod.type=='ARMATURE':mod.object=rig
body.parent=rig;body.matrix_world=world
for a in dst.actions:a.use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=str(W/'master_motion.blend'))
def run(n,*args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('transfer_uv.py',W/'master_motion.blend',P/'meshy/body_retexture_v1',W/'master_uv_body.blend')
run('transfer_uv.py',W/'master_uv_body.blend',P/'meshy/head_retexture_v1',W/'master_uv.blend','HeadUV')
run('uv_raster.py',W/'master_uv.blend','UVMap',1024)
run('uv_raster.py',W/'master_uv.blend','HeadUV',1024)
run('render_tex.py',W/'master_uv.blend',P/'meshy/body_retexture_v1/texture_urls_0_base_color.png','texture_raw',P/'meshy/head_retexture_v1/texture_urls_0_base_color.png')
