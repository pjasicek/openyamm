import bpy,bmesh,json,sys
import numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v1_parts.blend'))
parts=sorted((o for o in bpy.data.objects if o.type=='MESH'),key=lambda o:o.name)
# Meshy inflated the sash knot into a pouch; preserve its folds as a broad, shallow sash.
for v in bpy.data.objects['P07'].data.vertices:
 v.co.x*=1.9;v.co.y=-.145+(v.co.y+.145)*.40;v.co.z=1.025+(v.co.z-.971)*.48
# The small triangular shirt tail is an inward-folded placket, seated under the sash.
for v in bpy.data.objects['P09'].data.vertices:
 if v.co.z<1.14:v.co.y=max(v.co.y,-.115)

for o in parts:
 i=int(o.name[1:]);o.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[i]*len(o.data.vertices))
 for f in o.data.polygons:f.use_smooth=True
for o in bpy.data.objects:o.select_set(o in parts)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();body=bpy.context.object;body.name=body.data.name='Body'
me=body.data;bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
co=np.array([tuple(v.co) for v in me.vertices]);me.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',co.ravel())
pv=np.zeros(len(me.vertices),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
image=bpy.data.images.new('Provisional_Only',width=8,height=1,alpha=False)
colours=[(.76,.73,.65,1),(.36,.41,.47,1),(.40,.21,.10,1),(.60,.65,.77,1),(.55,.02,.025,1),(.11,.075,.042,1),(.8,.8,.8,1),(.06,.035,.018,1)]
image.pixels=[c for rgba in colours for c in rgba];image.pack()
mat=bpy.data.materials.new('Mep_Provisional');mat.use_nodes=True;nt=mat.node_tree;tex=nt.nodes.new('ShaderNodeTexImage');tex.image=image;tex.interpolation='Closest';bs=nt.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.85;nt.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
me.materials.clear();me.materials.append(mat);uv=me.uv_layers.active or me.uv_layers.new(name='UVMap')
for f in me.polygons:
 part=pv[f.vertices[0]];c=np.array(f.center);slot=1 if part==1 else 2 if part in (2,3,5,6) else 3 if part==4 else 4 if part in (7,8) or part>=14 else 5 if part in (10,11) else 7 if part in (12,13) else 0
 if part==0 and f.center.z>1.43:slot=2 if f.center.z>1.5 and f.center.y<.02 else 6
 for li in f.loop_indices:uv.data[li].uv=((slot+.5)/8,.5)
 f.material_index=0
assert np.isfinite(co).all() and len(co)>5000
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
for o in bpy.data.objects:o.select_set(o==body)
bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(p/'work/body_for_rig.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False,export_attributes=False)
common.workbench_clay(bpy.context.scene,textured=True)
common.render_views(str(p/'review/clean'),.85,2.05,views=('front','left','back','three_quarter'),resolution=(750,950))
