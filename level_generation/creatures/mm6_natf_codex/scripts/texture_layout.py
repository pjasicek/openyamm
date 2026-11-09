import bpy,json,sys,runpy,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_finished.blend'));body=bpy.data.objects['Body'];me=body.data;rig=bpy.data.objects['Rig'];pv=[a.value for a in me.attributes['piece'].data];changed=[]
for v in me.vertices:
 if pv[v.index]!=1:continue
 z=v.co.z;t=float(np.clip((z-.61)/.06,0,1))*float(np.clip((1.00-z)/.08,0,1))
 if t<=0:continue
 sd='L'if v.co.x>0 else'R';a=rig.data.bones[f'B_{sd}_Thigh'].head_local;b=rig.data.bones[f'B_{sd}_Calf'].head_local;d=b-a;u=float(np.clip((v.co-a).dot(d)/d.length_squared,0,1));r=v.co-(a+d*u);v.co-=r.normalized()*.007*t;changed.append(v.index)
with bpy.data.libraries.load(str(P/'work/head_uv_master.blend'))as(src,dst):dst.meshes=['Body']
ref=dst.meshes[0];assert len(ref.polygons)==len(me.polygons);flags=[v.value for v in ref.attributes['head'].data];(me.attributes.get('head')or me.attributes.new('head','INT','FACE')).data.foreach_set('value',flags);uv=me.uv_layers.new(name='HeadUV');uv.data.foreach_set('uv',[x for v in ref.uv_layers['HeadUV'].data for x in v.uv]);me.uv_layers.active=me.uv_layers['UVMap'];bpy.data.meshes.remove(ref);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/production_body.blend'))
(P/'work/concealed_leg_fit.json').write_text(json.dumps({'vertices':len(changed),'radial_inset_max_m':.007,'fade_height_m':[.61,.67,.92,1.0]},indent=2))
sys.argv=['transfer','--',str(P/'work/production_body.blend'),str(P/'meshy/body_retexture_v1'),str(P/'work/textured_master.blend')];runpy.run_path(str(P/'scripts/transfer_uv.py'),run_name='__main__')
for layer in ['UVMap','HeadUV']:
 sys.argv=['raster','--',str(P/'work/textured_master.blend'),layer,'1024'];runpy.run_path(str(P/'scripts/uv_raster.py'),run_name='__main__')
for layer,tag in [('UVMap','body'),('HeadUV','head')]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));body=bpy.data.objects['Body'];me=body.data;me.uv_layers.active=me.uv_layers[layer]
 import bmesh
 bm=bmesh.new();bm.from_mesh(me);bm.faces.ensure_lookup_table();hd=bm.faces.layers.int['head'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if bool(f[hd])!=(tag=='head')],context='FACES');bm.to_mesh(me);bm.free()
 bpy.context.scene.render.threads_mode='FIXED';bpy.context.scene.render.threads=4
 (P/'textures').mkdir(exist_ok=True);sys.argv=['ao','--','Body',str(P/f'textures/natf_{tag}_ao.png'),'.035','1024'];runpy.run_path(str(P.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
