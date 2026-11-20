import bpy,bmesh,json,sys,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/st_v1_parts.blend'))
parts=[o for o in bpy.data.objects if o.type=='MESH'];skin=bpy.data.objects['P00']
co=np.array([tuple(v.co) for v in skin.data.vertices]);nose=co[(co[:,2]>1.51)&(co[:,2]<1.69)];tip=nose[np.argsort(nose[:,1])[:12]].mean(0)
neck=co[(co[:,2]>1.46)&(co[:,2]<1.49)&(np.abs(co[:,0])<.09)];pivot=neck.mean(0);angle=math.atan2(tip[0]-pivot[0],-(tip[1]-pivot[1]))
print('HEAD yaw correction deg',-math.degrees(angle),'tip',tip,'neck pivot',pivot,flush=True)
assert abs(angle)<math.radians(50)
for v in skin.data.vertices:
 t=min(1,max(0,(v.co.z-1.40)/.15));t=t*t*(3-2*t)
 if t:v.co=Vector(pivot)+Matrix.Rotation(-angle*t,3,'Z')@(v.co-Vector(pivot))
# Keep collar outside the upper chest, where the raw shells intersected in two visible triangles.
from mathutils.bvhtree import BVHTree
bm=bmesh.new();bm.from_mesh(skin.data);tree=BVHTree.FromBMesh(bm)
for v in bpy.data.objects['P03'].data.vertices:
 pos,n,_,dist=tree.find_nearest(v.co)
 if pos is not None and dist<.04 and (v.co-pos).dot(n)<.006:v.co=pos+n*.006
bm.free()
# Keep the already symmetric headcloth in place.
for o in parts:
 n=int(o.name[1:]);a=o.data.attributes.new('piece','INT','POINT');a.data.foreach_set('value',[n]*len(o.data.vertices));o.select_set(True)
bpy.context.view_layer.objects.active=skin;bpy.ops.object.join();body=bpy.context.object;body.name=body.data.name='Body';body.data.materials.clear()
mat=bpy.data.materials.new('Neutral rig surface');mat.use_nodes=True;body.data.materials.append(mat)
im=bpy.data.images.new('Neutral rig texture',width=4,height=4);im.generated_color=(.45,.45,.45,1);im.pack();tx=mat.node_tree.nodes.new('ShaderNodeTexImage');tx.image=im;mat.node_tree.links.new(tx.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
if not body.data.uv_layers:body.data.uv_layers.new(name='UVMap')
for uv in body.data.uv_layers.active.data:uv.uv=(.5,.5)
orig=body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT');orig.data.foreach_set('vector',[x for v in body.data.vertices for x in v.co])
for o in list(bpy.data.objects):
 if o is not body:bpy.data.objects.remove(o,do_unlink=True)
assert len(body.data.vertices)>5000
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'work/body_for_rig.glb'),export_format='GLB',use_selection=True,export_animations=False,export_skins=False,export_attributes=False,export_yup=True)
common.workbench_clay(bpy.context.scene);common.render_views(str(P/'review/corrected'),.95,2.05,views=('front','left','three_quarter'),resolution=(600,900))
(P/'work/geometry_correction.json').write_text(json.dumps({'head_yaw_degrees':-math.degrees(angle),'pivot':pivot.tolist(),'triangles':sum(len(f.vertices)-2 for f in body.data.polygons),'piece_count':len(parts),'rationale':'Generated skull turned relative to the torso; infer neutral head axis from muzzle tip and neck ring, smoothly fade through neck'},indent=2))
