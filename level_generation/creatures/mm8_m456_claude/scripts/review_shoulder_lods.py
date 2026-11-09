"""Inspect the actual delivered shoulder surface and textures at every runtime LOD."""
import bpy,sys,math,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));sys.path.insert(0,str(P/'scripts'))
from run_gates import Glb,load_meshes
from common import setup_render,workbench_clay,ortho_camera
bpy.ops.wm.read_factory_settings(use_empty=True);g=Glb(P/'export/mm8_m456.glb');meshes=[m for m in load_meshes(g) if '/colour' in m.label]
sc=setup_render((600,600));workbench_clay(sc,True);out=P/'review/arm_pad_repair/lods';out.mkdir(exist_ok=True)
for m in meshes:
 uv=[];normals=[]
 for prim in g.doc['meshes'][m.index]['primitives']:
  uv.extend(g.accessor(prim['attributes']['TEXCOORD_0']));normals.extend(g.accessor(prim['attributes']['NORMAL']))
 uv=np.array(uv);uv[:,1]=1-uv[:,1];mi=g.doc['meshes'][m.index]['primitives'][0]['material'];mat=g.doc['materials'][mi];ti=mat['pbrMetallicRoughness']['baseColorTexture']['index'];im=g.doc['images'][g.doc['textures'][ti]['source']];bv=g.doc['bufferViews'][im['bufferView']];off=bv.get('byteOffset',0);path=Path('/tmp/dh-shoulder-atlas.png');path.write_bytes(g.data[off:off+bv['byteLength']])
 material=bpy.data.materials.new('body');material.use_nodes=True;t=material.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(path));material.node_tree.nodes.active=t
 for name,time in [('Standing',0),('Running',.333333),('Attack',.333333),('Hit',.233333),('Fidget',1.433333),('Death',2.166667)]:
  clip=next(a for n,a,s,e in g.clips() if n==name);pose=g.pose(clip,np.array([time]))[0];co=m.posed(pose);me=bpy.data.meshes.new('review');me.from_pydata(co.tolist(),[],m.faces.tolist());me.update();me.materials.append(material);layer=me.uv_layers.new()
  for face in me.polygons:
   face.use_smooth=True
   for li in face.loop_indices:layer.data[li].uv=uv[me.loops[li].vertex_index]
  N=np.zeros_like(co);M=pose[m.skin_nodes]@m.bind
  for k in range(m.weights.shape[1]):N+=np.einsum('nij,nj->ni',M[m.joints[:,k],:3,:3],normals)*m.weights[:,k,None]
  N/=np.maximum(np.linalg.norm(N,axis=1,keepdims=True),1e-9);me.normals_split_custom_set_from_vertices(N.tolist())
  ob=bpy.data.objects.new('review',me);sc.collection.objects.link(ob)
  c=pose[g.names['B_Spine2'],:3,3].copy();c[2]-=.02
  from mathutils import Vector
  c=Vector(c)
  for side,a in [('left',125),('right',-125)]:
   rad=math.radians(a);cam=ortho_camera('camera',(c.x+math.sin(rad)*5,c.y-math.cos(rad)*5,c.z+.08),(0,0,0),.65);cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam;sc.render.filepath=str(out/f'LOD{m.label[-1]}_{name}_{side}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
  bpy.data.objects.remove(ob,do_unlink=True);bpy.data.meshes.remove(me)
