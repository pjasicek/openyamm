"""Fit detailed head and test the playbook's connected-head projection before committing a graft."""
from pathlib import Path
import bpy,bmesh,sys,json,math,numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v8.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
with bpy.data.libraries.load(str(p/'work/head_return_v2.blend'),link=False) as (src,dst):dst.objects=src.objects
source=max((o for o in dst.objects if o.type=='MESH'),key=lambda o:len(o.data.vertices))
bpy.context.collection.objects.link(source);source.name='HeadSource'
scale=.13972;offset=Vector((-.00733,.016,1.56716))
for v in source.data.vertices:v.co=v.co*scale+offset
source.data.update()
# Preserve source as a separate fitted checkpoint for projection and possible silhouette repairs.
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/head_fitted_v2.blend'))
bm=bmesh.new();bm.from_mesh(body.data);hd=bm.faces.layers.int['head'];pv=bm.verts.layers.int['piece']
faces=[f for f in bm.faces if f[hd]];edges={e for f in faces for e in f.edges if all(x[hd] for x in e.link_faces)}
bmesh.ops.subdivide_edges(bm,edges=list(edges),cuts=1,use_grid_fill=True)
bm.verts.ensure_lookup_table()
tree=BVHTree.FromObject(source,bpy.context.evaluated_depsgraph_get(),deform=False)
# The mouth corners and dental tusks changed position; the old geometry is first fitted to that neighbourhood.
old_tusks={part:[v for v in bm.verts if v[pv]==part] for part in [20,21]}
for part,verts in old_tusks.items():
 for v in verts:
  # The native tusks rise from the lip rather than the bottom of the jaw.
  v.co.z+=.024;v.co.y-=.016
# Only head faces move. Keep the shared neck edge and feather its neighbouring band.
headverts={v for f in bm.faces if f[hd] for v in f.verts};moved=[]
for v in headverts:
 w=min(max((v.co.z-1.44)/.035,0),1);w=w*w*(3-2*w)
 loc,n,idx,d=tree.find_nearest(v.co)
 if loc is not None:
  moved.append(float((loc-v.co).length*w));v.co=v.co.lerp(loc,w)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free();body.data.update()
source.hide_render=True;source.hide_set(True)
common.workbench_clay(bpy.context.scene);common.render_views(str(p/'revision_02/head_projected_clay'),1.575,.40,views=('front','left','three_quarter'),resolution=(600,600))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v9_projection.blend'))
print('HEAD_PROJECTED',len(headverts),'max displacement',max(moved),'tris',sum(len(f.vertices)-2 for f in body.data.polygons))
