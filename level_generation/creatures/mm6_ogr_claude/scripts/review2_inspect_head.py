from pathlib import Path
import bpy,bmesh,numpy as np,sys,json
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v8.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
me=body.data;hd=me.attributes['head'];ids=sorted({i for f in me.polygons if hd.data[f.index].value for i in f.vertices});old=np.array([tuple(me.vertices[i].co) for i in ids]);print('OLD_HEAD',len(ids),old.min(0),old.max(0))
for name in ['B_Head','B_Neck','B_Spine2']:print('BONE',name,list(rig.data.bones[name].head_local),list(rig.data.bones[name].tail_local))
for part in [20,21]:
 cs=np.array([tuple(v.co) for v in me.vertices if me.attributes['piece'].data[v.index].value==part]);print('TUSK',part,cs.min(0),cs.max(0))
common.workbench_clay(bpy.context.scene);common.render_views(str(p/'revision_02/old_head_clay'),1.575,.4,views=('front','left','three_quarter'),resolution=(500,500))
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.import_scene.gltf(filepath=str(p/'meshy/head_model_v2/model_urls_glb.glb'))
heads=[o for o in bpy.data.objects if o.type=='MESH'];co=np.array([tuple(o.matrix_world@v.co) for o in heads for v in o.data.vertices]);print('NEW_HEAD',len(co),'tri',sum(len(f.vertices)-2 for o in heads for f in o.data.polygons),co.min(0),co.max(0))
for o in heads:
 o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
common.workbench_clay(bpy.context.scene,textured=True);common.render_views(str(p/'revision_02/head_return'),float((co.max(0)[2]+co.min(0)[2])/2),float(np.ptp(co,axis=0).max()*1.1),views=('front','left','back','right','three_quarter'),resolution=(600,600))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/head_return_v2.blend'))
