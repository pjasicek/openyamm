import bpy,runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_preprops.blend'));me=bpy.data.objects['Body'].data;pv=[x.value for x in me.attributes['piece'].data]
a=me.attributes.get('head')or me.attributes.new('head','INT','FACE');a.data.foreach_set('value',[int(pv[f.vertices[0]]==200)for f in me.polygons])
src=me.uv_layers.active;dest=me.uv_layers.new(name='HeadUV')
for i,u in enumerate(src.data):dest.data[i].uv=u.uv
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_uv0.blend'))
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('transfer_uv.py',P/'work/rig_uv0.blend',P/'meshy/body_retexture_v1',P/'work/rig_uv.blend')
run('uv_raster.py',P/'work/rig_uv.blend','UVMap','1024')
run('uv_raster.py',P/'work/rig_uv.blend','HeadUV','1024')
