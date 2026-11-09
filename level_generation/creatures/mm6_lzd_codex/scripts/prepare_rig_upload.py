"""Short native tail, remove isolated junk, preserve weighted topology until post-rig reduction."""
import bpy,json,sys,math
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/st_v1_parts.blend'))
for n in ['P106','P107']:
 if n in bpy.data.objects:bpy.data.objects.remove(bpy.data.objects[n],do_unlink=True)
parts=[o for o in bpy.data.objects if o.type=='MESH']
for ob in parts:
 n=int(ob.name[1:]);attr=ob.data.attributes.new('piece','INT','POINT');attr.data.foreach_set('value',[n]*len(ob.data.vertices))
 for v in ob.data.vertices:
  if n==1 and v.co.y>-.25:
   # Meshy inferred a long dragon tail; source tail is one forearm long.
   v.co.y=-.25+(v.co.y+.25)*.32
  v.co.y+=.42
 ob.select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects['P01'];bpy.ops.object.join();body=bpy.context.object;body.name=body.data.name='Body'
orig=body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT');orig.data.foreach_set('vector',[x for v in body.data.vertices for x in v.co])
body.data.materials.clear();mat=bpy.data.materials.new('Neutral rig surface');mat.use_nodes=True;body.data.materials.append(mat)
im=bpy.data.images.new('Neutral rig texture',width=4,height=4);im.generated_color=(.45,.45,.45,1);im.pack();tx=mat.node_tree.nodes.new('ShaderNodeTexImage');tx.image=im;mat.node_tree.links.new(tx.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
if not body.data.uv_layers:body.data.uv_layers.new(name='UVMap')
for uv in body.data.uv_layers.active.data:uv.uv=(.5,.5)
for o in list(bpy.data.objects):
 if o is not body:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'work/body_for_rig.glb'),export_format='GLB',use_selection=True,export_animations=False,export_skins=False,export_attributes=False,export_yup=True)
scene=bpy.context.scene;common.workbench_clay(scene)
common.render_views(str(P/'review/clean_body'),.85,2.05,views=('front','left','back','three_quarter'),resolution=(800,900))
common.render_views(str(P/'review/clean_head'),1.52,.48,views=('front','left','three_quarter'),resolution=(700,700),target=(0,-.10))
co=np.array([tuple(v.co)for v in body.data.vertices]);pv=np.array([x.value for x in body.data.attributes['piece'].data])
for side,piece in [('L',3),('R',4)]:
 mask=(pv==piece)&(np.abs(co[:,0])>.52);centre=Vector(co[mask].mean(0))
 for view,direction in [('palm',(0,-1,0)),('back',(0,1,0)),('outer',(1 if side=='L' else -1,0,0))]:
  d=Vector(direction);cam=common.ortho_camera('hand',centre+d,(0,0,0),.3);cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();scene.camera=cam;scene.render.resolution_x=scene.render.resolution_y=700;scene.render.filepath=str(P/f'review/rest_hand_{side}_{view}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
report={'triangles':sum(len(f.vertices)-2 for f in body.data.polygons),'vertices':len(body.data.vertices),'bounds':[co.min(0).tolist(),co.max(0).tolist()],'tail_length_m':float(co[(pv==1),1].max()-.17),'removed_junk_parts':[106,107]}
assert .28<report['tail_length_m']<.35,report
(P/'work/cleanup_report.json').write_text(json.dumps(report,indent=2));print('CLEAN',report)
