import bpy,bmesh,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common,round1_materials as M
regions={}
for state,path in [('before','review/round3/before'),('after','work')]:
 regions[state]={}
 for level,file in enumerate(['production_master','round1_lod1','round1_lod2','round1_lod3']):
  bpy.ops.wm.open_mainfile(filepath=str(P/f'{path}/{file}.blend'));o=bpy.data.objects['Body'];me=o.data
  regions[state][level]={'positions':[v.co[:] for v in me.vertices],'piece':[a.value for a in me.attributes['piece'].data]}
(P/'review/round3/native_regions.json').write_text(json.dumps(regions))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/production_master.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];ax=bpy.data.objects['AxeMesh'];M.setup(b,ax,directory=P/'textures/round1_rebaked',rebaked=True)
ax.hide_render=True
bm=bmesh.new();bm.from_mesh(b.data);pv=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if any(v[pv]!=0 for v in f.verts)],context='FACES');bm.to_mesh(b.data);bm.free()
sc=bpy.context.scene;common.workbench_clay(sc,textured=True);sc.view_settings.view_transform='Standard';sc.display.shading.studiolight_rotate_z=.6
for role,time in [('Standing',0),('Attack',.95)]:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(int(time*240),subframe=time*240%1)
 for textured in [True,False]:
  common.workbench_clay(sc,textured=textured)
  common.render_views(str(P/f'review/round3/skin_{role}_{textured}'),.9,.80,views=['front','back'],resolution=(640,640))
