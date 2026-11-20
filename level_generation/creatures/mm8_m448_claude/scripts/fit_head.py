"""Fit the separately generated head at the neck; inspect before selecting the graft."""
from pathlib import Path
import sys
import json
import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'scripts'))
import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/body_clean.blend'))
body=bpy.data.objects['Body']
# Cut across the neck, retaining the hunched back, shoulder caps and shirt.
bm=bmesh.new();bm.from_mesh(body.data)
piece=bm.verts.layers.int['piece']
remove=[]
for v in bm.verts:
    x,y,z=v.co;pid=v[piece]
    if pid==0:
        cut=(z>1.42 and y<-.15 and abs(x)<.16) or (z>1.32 and y<-.22)
    elif pid==1:
        cut=z>1.50 and y<-.10
    else:
        cut=pid in (4,5,6,78) or (z>1.48 and y<-.10)
    if cut:remove.append(v)
bmesh.ops.delete(bm,geom=remove,context='VERTS')
bm.to_mesh(body.data);bm.free()
body_tree=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get(),deform=False)
before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(p/'meshy/head_geometry_v1/model_urls_glb.glb'))
new=set(bpy.data.objects)-before
head=next(o for o in new if o.type=='MESH')
for o in new:
    if o is not head:bpy.data.objects.remove(o,do_unlink=True)
for o in bpy.data.objects:o.select_set(o is head)
bpy.context.view_layer.objects.active=head
head.parent=None
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
for v in head.data.vertices:
    v.co = v.co*0.4+Vector((0,-0.21,1.5))
    t=max(0,min(1,(1.50-v.co.z)/0.13))
    v.co.y += 0.13*t*t*(3-2*t)
bm=bmesh.new();bm.from_mesh(head.data)
bmesh.ops.bisect_plane(bm,geom=bm.verts[:]+bm.edges[:]+bm.faces[:],plane_co=(0,0,1.435),plane_no=(0,0,1),clear_inner=True)
# Bury the bottom neck band in the original torso, as in the playbook's graft.
for v in bm.verts:
    t=max(0,min(1,(1.475-v.co.z)/0.04))
    if not t:continue
    loc,norm,_,distance=body_tree.find_nearest(v.co)
    if loc is not None and distance<0.16:
        v.co=v.co.lerp(loc-norm*0.003,t*t*(3-2*t))
bm.to_mesh(head.data);bm.free()
head.data.materials.clear()
head.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[200]*len(head.data.vertices))
head.name='Head'
for ob in [body,head]:
    if 'orig_co' in ob.data.attributes:ob.data.attributes.remove(ob.data.attributes['orig_co'])
    for f in ob.data.polygons:f.use_smooth=True
for o in bpy.data.objects:o.select_set(o in (body,head))
bpy.context.view_layer.objects.active=body
bpy.ops.object.join()
co=np.array([tuple(v.co) for v in body.data.vertices])
body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',co.ravel())
assert np.isfinite(co).all() and 1.65<co[:,2].max()<1.75
common.workbench_clay(bpy.context.scene)
bpy.context.scene.display.shading.color_type='SINGLE'
bpy.context.scene.display.shading.single_color=(0.65,0.65,0.65)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/body_head_v1.blend'))
common.render_views(str(p/'review/graft_v1'),0.85,1.95,views=('front','three_quarter','left','back'),resolution=(1000,1000))
common.render_views(str(p/'review/graft_head_v1'),1.5,0.6,views=('front','three_quarter','left','back'),resolution=(650,650),target=(0,-0.18))
print('GRAFT',len(co),'vertices',sum(len(f.vertices)-2 for f in body.data.polygons),'triangles')
