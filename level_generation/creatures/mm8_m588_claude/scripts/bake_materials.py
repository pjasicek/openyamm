"""Bake stone crevice AO and capture the frozen atlas surface coordinates."""
import bpy,sys,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];N=1024
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig.blend'))
body=bpy.data.objects['Body'];me=body.data;uv=me.uv_layers.active.data
co=np.array([tuple(v.co) for v in me.vertices]);piece_ids=np.array([v.value for v in me.attributes['piece'].data])
piece=np.full((N,N),-1,np.int32);pos=np.zeros((N,N,3),np.float32);normal=np.zeros_like(pos)
me.calc_loop_triangles()
for tri in me.loop_triangles:
 v=list(tri.vertices);p=np.array([tuple(uv[l].uv) for l in tri.loops])*N
 lo=np.maximum(np.floor(p.min(0)).astype(int),0);hi=np.minimum(np.ceil(p.max(0)).astype(int),N-1)
 xs,ys=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5)
 a,b,c=p;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
 assert abs(den)>1e-8
 w0=((b[1]-c[1])*(xs-c[0])+(c[0]-b[0])*(ys-c[1]))/den
 w1=((c[1]-a[1])*(xs-c[0])+(a[0]-c[0])*(ys-c[1]))/den;w2=1-w0-w1
 mask=(w0>=0)&(w1>=0)&(w2>=0)
 iy=(N-1-(ys[mask]-.5)).astype(int);ix=(xs[mask]-.5).astype(int)
 piece[iy,ix]=piece_ids[v[0]];pos[iy,ix]=w0[mask,None]*co[v[0]]+w1[mask,None]*co[v[1]]+w2[mask,None]*co[v[2]]
 normal[iy,ix]=tuple(tri.normal)
np.savez_compressed(P/'work/uv_surface.npz',piece=piece,pos=pos,normal=normal)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=32
if sc.world is None:sc.world=bpy.data.worlds.new('World')
sc.world.light_settings.distance=.07
im=bpy.data.images.new('RockCreviceAO',width=N,height=N,alpha=False)
mat=bpy.data.materials.new('AO_Bake');mat.use_nodes=True;node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;mat.node_tree.nodes.active=node
me.materials.clear();me.materials.append(mat)
for ob in bpy.data.objects:ob.select_set(ob==body)
bpy.context.view_layer.objects.active=body;sc.render.bake.margin=12;sc.render.bake.use_selected_to_active=False
bpy.ops.object.bake(type='AO');im.filepath_raw=str(P/'work/ao.png');im.file_format='PNG';im.save()
print('AO complete; atlas coverage',float((piece>=0).mean()))
