import bpy,bmesh,sys,json,math,subprocess,shutil,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C,reduction_bake as B
from reduction_render import render
rows=[]
for scale in [1.,1.015,.99]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/lod3_edge88clip15.blend'));C.reset();r=bpy.data.objects['Rig'];old=bpy.data.objects['BucklerMesh'];mat=old.data.materials[0];bpy.data.objects.remove(old,do_unlink=True);N=16;v=[(0,-.052,0)];f=[]
 for rad,y in [(.65,-.032),(.94,-.008),(1.,-.005),(1.,.013)]:
  for i in range(N):a=i*math.tau/N;v.append((.189*rad*math.cos(a)*scale,y,.244*rad*math.sin(a)*scale))
 for i in range(N):f.append((0,1+i,1+(i+1)%N))
 for j in range(3):
  for i in range(N):a=1+j*N+i;b=1+j*N+(i+1)%N;f.append((a,b,b+N,a+N))
 back=len(v);v.append((0,-.040,0))
 for i in range(N):f.append((back,1+3*N+(i+1)%N,1+3*N+i))
 for z in [-.09,.09]:
  off=len(v)
  for x,y in [(-.13,.02),(0,.075),(.13,.02)]:
   for dz,dy in [(-.026,0),(.026,0),(.026,.005),(-.026,.005)]:v.append((x,y+dy,z+dz))
  for j in range(2):
   for k in range(4):a=off+j*4+k;b=off+j*4+(k+1)%4;f.append((a,b,b+4,a+4))
 me=bpy.data.meshes.new('BucklerMesh');M=r.data.bones['Buckler'].matrix_local;me.from_pydata([M@Vector(x)for x in v],[],f);me.update();o=bpy.data.objects.new('BucklerMesh',me);bpy.context.collection.objects.link(o);me.materials.append(mat);o.vertex_groups.new(name='Buckler').add(list(range(len(v))),1,'REPLACE');o.parent=r;mod=o.modifiers.new('Rig','ARMATURE');mod.object=r
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.01);bpy.ops.object.mode_set(mode='OBJECT');tag=f'shield{round(scale*1000)}';tex=P/f'work/reduction/lod3_{tag}';shutil.copytree(P/'work/reduction/lod3_continuous',tex,dirs_exist_ok=True);B.bake(o,tex/'buckler');subprocess.run(['/usr/bin/python3','-B',str(P/'scripts/tier_previews.py'),str(tex)],check=True);dest=P/f'work/lod3_{tag}.blend';tris=C.triangles(o);assert tris<=167,tris;bpy.ops.wm.save_as_mainfile(filepath=str(dest));out=P/f'review/reduction/lod3_{tag}';render(dest,out,tex,88)
 d=json.loads(subprocess.check_output(['/usr/bin/python3','-B',str(P/'scripts/reduction_metrics.py'),str(P/'review/reduction/lod3_reference'),str(out)],text=True));rr=list(d['views'].values());uu=[(x['reference_pixels']+x['candidate_pixels'])/(1+x['iou'])for x in rr];pooled=sum(x['iou']*u for x,u in zip(rr,uu))/sum(uu);rows.append({'scale':scale,'blend':str(dest.relative_to(P)),'textures':str(tex.relative_to(P)),'triangles':tris,'pooled_iou':pooled,'visual':d});(P/'review/reduction/shield_curve.json').write_text(json.dumps(rows,indent=2));print('SHIELD',scale,tris,pooled,flush=True)
 if pooled>=.971:break
