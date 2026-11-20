import bpy,bmesh,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm6_wyrm.blend'))
body=bpy.data.objects['Wyrm'];rig=bpy.data.objects['Wyrm_Rig'];me=body.data;sc=bpy.context.scene
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
bounds=[e for e in bm.edges if e.is_boundary]
print('TOPOLOGY',len(me.vertices),len(me.polygons),'custom normals',me.has_custom_normals,'boundary',len(bounds),'nonmanifold',sum(not e.is_manifold for e in bm.edges))
print('BOUNDARY CHEST',[(e.index,[list(v.co) for v in e.verts]) for e in bounds if any(-.4<v.co.y<-.28 and .1<v.co.z<.23 for v in e.verts)])
co=np.array([v.co[:] for v in me.vertices]);weights=np.zeros((len(co),len(body.vertex_groups)))
for v in me.vertices:
 for g in v.groups:weights[v.index,g.group]=g.weight
np.savez('/tmp/wyrm-junction-mesh.npz',co=co,faces=np.array([list(f.vertices) for f in me.polygons]),weights=weights,names=np.array([g.name for g in body.vertex_groups]),normals=np.array([f.normal[:] for f in me.polygons]))
sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=1000;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.6,.64,.59);sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH';sc.display.shading.show_shadows=False
for o in sc.objects:
 if o.type=='MESH' and o!=body:o.hide_render=True
cam=bpy.data.objects.new('JunctionCamera',bpy.data.cameras.new('JunctionCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.22
for label,loc in [('front',(0,-1,.17)),('quarter',(.4,-1,.23))]:
 cam.location=loc;cam.rotation_euler=(Vector((0,-.345,.17))-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath='/tmp/wyrm-junction-'+label+'.png';bpy.ops.render.render(write_still=True)
