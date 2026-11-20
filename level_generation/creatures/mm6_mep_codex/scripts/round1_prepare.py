import bpy,json,sys,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/final_lod{level}.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];me=b.data
 print('LOD',level,'attributes',[(a.name,a.domain) for a in me.attributes],flush=True)
 if level==0:
  info={'bones':{n:{'head':list(v.head_local),'matrix':[list(x) for x in v.matrix_local]} for n,v in r.data.bones.items()},'hands':{}}
  for s in 'LR':
   h=r.data.bones[f'B_{s}_Hand'];f=r.data.bones[f'B_{s}_Finger2'].head_local-h.head_local;t=r.data.bones[f'B_{s}_Finger1'].head_local-r.data.bones[f'B_{s}_Finger4'].head_local;normal=f.cross(t).normalized()
   if normal.y>0:normal=-normal
   info['hands'][s]={'palm_axis':list(h.matrix_local.to_3x3().inverted()@normal),'fingers':[f'B_{s}_Finger{i}' for i in range(5)]}
  (P/'work/round1_rig.json').write_text(json.dumps(info,indent=2))
 uv=me.uv_layers['MergedUV'].data;me.calc_loop_triangles();pv=np.array([x.value for x in me.attributes['piece'].data]);N=[1024,1024,512,256][level]
 for mi,mat in enumerate(me.materials):
  prefix='mep_head' if 'Head' in mat.name else 'mep_staff' if 'Staff' in mat.name else 'mep'
  piece=np.full((N,N),-1,np.int16);pos=np.zeros((N,N,3),np.float32)
  for tri in me.loop_triangles:
   if tri.material_index!=mi:continue
   xy=np.array([uv[i].uv[:] for i in tri.loops])*N;v=np.array([me.vertices[i].co[:] for i in tri.vertices]);a,bb,c=xy;den=(bb[1]-c[1])*(a[0]-c[0])+(c[0]-bb[0])*(a[1]-c[1])
   if abs(den)<1e-9:continue
   lo=np.maximum(0,np.floor(xy.min(0)).astype(int));hi=np.minimum(N-1,np.ceil(xy.max(0)).astype(int));xs,ys=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5)
   w0=((bb[1]-c[1])*(xs-c[0])+(c[0]-bb[0])*(ys-c[1]))/den;w1=((c[1]-a[1])*(xs-c[0])+(a[0]-c[0])*(ys-c[1]))/den;w2=1-w0-w1;m=(w0>=0)&(w1>=0)&(w2>=0);iy=(N-ys[m]-.5).astype(int);ix=(xs[m]-.5).astype(int);piece[iy,ix]=pv[tri.vertices[0]];pos[iy,ix]=w0[m,None]*v[0]+w1[m,None]*v[1]+w2[m,None]*v[2]
  np.savez_compressed(P/f'work/round1_{prefix}_lod{level}.npz',piece=piece,pos=pos)
