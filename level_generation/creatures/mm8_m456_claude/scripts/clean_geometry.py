"""Remove measured generator spikes; preserve separate armour shells and fit the narrow native crest."""
from pathlib import Path
import bpy,bmesh,json,sys
import numpy as np
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v1_parts.blend'))
for name in ['P33','P34']:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
report={}
for obj in [o for o in bpy.data.objects if o.type=='MESH']:
 bm=bmesh.new();bm.from_mesh(obj.data)
 pred={'P00':lambda c:c.x < -.16 and c.z > .97,'P02':lambda c:c.z>1.0,'P05':lambda c:c.z>.94,'P12':lambda c:c.x<-.20,'P27':lambda c:c.z>.70}.get(obj.name)
 bad=[v for v in bm.verts if pred and pred(v.co)]
 if bad:bmesh.ops.delete(bm,geom=bad,context='VERTS')
 # Close only small holes; open armour rims remain under overlapping pieces.
 edges={e for e in bm.edges if e.is_boundary};loops=[]
 while edges:
  seed=edges.pop();component={seed};stack=[seed]
  while stack:
   edge=stack.pop()
   for vertex in edge.verts:
    for other in vertex.link_edges:
     if other in edges:edges.remove(other);component.add(other);stack.append(other)
  verts=set(v for e in component for v in e.verts);cen=sum((v.co for v in verts),common.Vector())/len(verts)
  loops.append({'edges':len(component),'centre':list(cen)})
  if len(component)<=20 and obj.name in ['P00','P02','P04','P05','P15','P27']:
   bmesh.ops.holes_fill(bm,edges=list(component),sides=0)
 if obj.name in ['P11','P13']:
  for v in bm.verts:
   if obj.name=='P11':v.co.x=-.006+(v.co.x+.006)*.30
   if v.co.y>.02:v.co.y=.02+(v.co.y-.02)*.60
   if v.co.z<1.50:v.co.z=1.50+(v.co.z-1.50)*.45
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces))
 bm.to_mesh(obj.data);bm.free();report[obj.name]={'deleted_vertices':len(bad),'boundaries_before_fill':loops}
 # A coarse diagnostic material atlas for Meshy's joint estimation; final texturing follows deformation review.
 idx=int(obj.name[1:]);obj.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[idx]*len(obj.data.vertices))
 colour=(.32,.35,.36,1)
 if idx==1:colour=(.55,.34,.22,1)
 if idx in [11]:colour=(.04,.20,.07,1)
 if idx in [12,13,14,19,24,25,26]:colour=(.55,.36,.10,1)
 if idx in [6,7]:colour=(.10,.12,.12,1)
 if idx in [29,30]:colour=(.25,.20,.12,1)
 image=bpy.data.images.new('provisional_'+obj.name,width=2,height=2);image.pixels[:]=list(colour)*4;image.pack()
 mat=bpy.data.materials.new('provisional_'+obj.name);mat.use_nodes=True;shader=mat.node_tree.nodes.get('Principled BSDF');tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;mat.node_tree.links.new(tex.outputs['Color'],shader.inputs['Base Color']);mat.diffuse_color=colour
 obj.data.materials.clear();obj.data.materials.append(mat)
 uv=obj.data.uv_layers.active or obj.data.uv_layers.new(name='UVMap')
 for v in uv.data:v.uv=(.5,.5)
for obj in bpy.data.objects:obj.select_set(obj.type=='MESH')
bpy.context.view_layer.objects.active=bpy.data.objects['P00'];bpy.ops.object.join();body=bpy.context.object;body.name=body.data.name='Body'
co=np.array([v.co[:] for v in body.data.vertices]);body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',co.ravel())
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(p/'work/body_for_rig.glb'),export_format='GLB',use_selection=True,export_animations=False)
common.workbench_clay(bpy.context.scene);bpy.context.scene.display.shading.color_type='MATERIAL'
common.render_views(str(p/'review/clean'),.85,1.85,views=('front','three_quarter','left','back'),resolution=(600,900))
(p/'review/geometry_cleanup.json').write_text(json.dumps(report,indent=2)+'\n')
print('CLEAN',len(body.data.polygons),'triangles')
