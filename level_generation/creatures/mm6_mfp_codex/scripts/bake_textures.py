import bpy,bmesh,sys,runpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));body=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();pv=np.array([x.value for x in body.data.attributes['piece'].data]);co=[v.co.copy()for v in body.data.vertices];fl=[f.vertices[:]for f in body.data.polygons if pv[f.vertices[0]]==4];tree=BVHTree.FromPolygons(co,fl);count=0
for v in body.data.vertices:
 if pv[v.index]!=5:continue
 distance=(v.co-Vector((-.279,-.056,1.022))).length
 if distance>=.060:continue
 p=v.co.copy();p.x=-p.x;loc,no,idx,d=tree.find_nearest(p)
 if loc is not None:
  loc.x=-loc.x;w=min(1,max(0,(.060-distance)/.020));v.co=v.co.lerp(loc,w);count+=1
print('FOREARM_SURFACE_REPAIR',count,'vertices matched to mirrored intact arm')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'))
for label,layer in [('body','UVMap'),('head','HeadUV')]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));body=bpy.data.objects['Body']
 for ob in bpy.data.objects:
  if ob.type=='MESH'and ob!=body:ob.hide_render=True
 bm=bmesh.new();bm.from_mesh(body.data);hd=bm.faces.layers.int['head'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if bool(f[hd])!=(label=='head')],context='FACES');bm.to_mesh(body.data);bm.free();body.data.uv_layers.active=body.data.uv_layers[layer];body.data.uv_layers.active.active_render=True
 sys.argv=['bake_creature_ao.py','--','Body',str(P/f'work/ao_{label}.png'),'.03','1024'];runpy.run_path(str(P.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
