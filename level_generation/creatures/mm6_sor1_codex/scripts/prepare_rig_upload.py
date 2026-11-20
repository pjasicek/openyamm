import bpy,bmesh,json,sys
from pathlib import Path
from collections import deque
import numpy as np
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/step1.blend'));ob=bpy.data.objects['Body']
bm=bmesh.new();bm.from_mesh(ob.data);pv=bm.verts.layers.int['piece'];bad=[]
for f in bm.faces:
 piece=f.verts[0][pv];co=np.array([v.co[:] for v in f.verts]);z=co[:,2];x=co[:,0]
 if (piece in (2,13,15) and z.min()<1.35) or (piece==3 and x.max()>-.35) or (piece==11 and z.min()<1.30) or (piece==0 and z.max()<.10 and x.max()-x.min()>.14):bad.append(f)
bmesh.ops.delete(bm,geom=bad,context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
# Separate connected skirt/shoe components after removing the return's false bridges.
seen=set();comps=[]
for v in bm.verts:
 if v[pv]!=0 or v in seen:continue
 q=[v];comp=[];seen.add(v)
 while q:
  a=q.pop();comp.append(a)
  for e in a.link_edges:
   b=e.other_vert(a)
   if b[pv]==0 and b not in seen:seen.add(b);q.append(b)
 co=np.array([v.co[:] for v in comp]);pid=100 if co[:,2].max()>.3 else (101 if co[:,0].mean()<0 else 102)
 for v in comp:v[pv]=pid
 comps.append({'id':pid,'vertices':len(comp),'lo':co.min(0).tolist(),'hi':co.max(0).tolist()})
bm.to_mesh(ob.data);bm.free();print('CLEAN2',len(bad),'faces; lower components',comps,flush=True)
(p/'work/lower_components.json').write_text(json.dumps(comps,indent=2))
assert any(c['id']==100 for c in comps)
# Keep the generated eyes, avoiding open sockets; the face/eyeballs get the head texture together.
co=np.array([v.co[:] for v in ob.data.vertices]);ob.data.attributes['orig_co'].data.foreach_set('vector',co.ravel())
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
mat=bpy.data.materials.new('RigProvisional');mat.use_nodes=True
image=bpy.data.images.new('RigNeutral',width=4,height=4);image.pixels=[.6,.6,.6,1]*16;image.pack()
node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image
mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
ob.data.materials.clear();ob.data.materials.append(mat)
if not ob.data.uv_layers:ob.data.uv_layers.new(name='UVMap')
for uv in ob.data.uv_layers.active.data:uv.uv=(.5,.5)
for o in bpy.data.objects:o.select_set(o==ob)
bpy.context.view_layer.objects.active=ob
bpy.ops.export_scene.gltf(filepath=str(p/'work/body_for_rig.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False,export_yup=True)
common.workbench_clay(bpy.context.scene);common.render_views(str(p/'review/clean_v2'),.85,1.9,views=('front','left'),resolution=(600,900))
