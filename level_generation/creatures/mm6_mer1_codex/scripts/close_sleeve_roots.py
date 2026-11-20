import bpy,bmesh,sys,numpy as np,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
bm=bmesh.new();bm.from_mesh(o.data);part=bm.verts.layers.int['piece'];uv=bm.loops.layers.uv.active;deform=bm.verts.layers.deform.active;head=bm.faces.layers.int['head'];created=[]
cov=np.load(P/'work/uvraster_UVMap.npz')['piece']>=0;patches=[]
def free_rect():
 for y in range(4,984,8):
  for x in range(4,884,8):
   if not cov[y:y+40,x:x+136].any():cov[y:y+40,x:x+136]=True;return x+4,y+4,128,32
 raise RuntimeError('No spare sleeve chart space')

for sd,pid in [('R',8),('L',9)]:
 edges=[e for e in bm.edges if e.is_boundary and all(v[part]==pid for v in e.verts) and min(v.co.z for v in e.verts)>1.18];verts=set(v for e in edges for v in e.verts);axis=(r.data.bones[f'B_{sd}_Forearm'].head_local-r.data.bones[f'B_{sd}_UpperArm'].head_local).normalized();mapping={};assert len(edges)>10
 for v in verts:
  shoulder=r.data.bones[f'B_{sd}_UpperArm'].head_local;nv=bm.verts.new(shoulder+(v.co-shoulder)*.30+Vector((-.06 if sd=='L'else .06,0,-.025)));nv[part]=pid
  for gi,w in v[deform].items():nv[deform][gi]=w
  mapping[v]=nv
 rect=free_rect();print("SLEEVE UV",sd,rect,flush=True)
 for ei,e in enumerate(edges):
  a,b=e.verts;host=e.link_faces[0];values={l.vert:l[uv].uv.copy()for l in host.loops};f=bm.faces.new((a,b,mapping[b],mapping[a]));f[head]=0;f.material_index=0
  x,y,w,h=rect;u0=(x+ei*w/len(edges))/1024;u1=(x+(ei+1)*w/len(edges))/1024;v0=1-y/1024;v1=1-(y+h)/1024
  for loop,coord in zip(f.loops,[(u0,v0),(u1,v0),(u1,v1),(u0,v1)]):loop[uv].uv=coord
  patches.append({'rect':[x+ei*w/len(edges),y,w/len(edges),h],'uv_a':list(values[a]),'uv_b':list(values[b])})
  created.append(f)
bmesh.ops.recalc_face_normals(bm,faces=created);bmesh.ops.triangulate(bm,faces=created);bm.to_mesh(o.data);bm.free();# Give the added under-trim charts the adjoining native cloth texels, with cavity darkening inward.
for path in sorted((P/'textures').glob('*.png')):
 if not (path.name.startswith('mer1_body_') or path.name in ['mer1_region_mask.png','mer1_a_preview.png','mer1_b_preview.png','mer1_c_preview.png']):continue
 im=bpy.data.images.load(str(path),check_existing=False);im.colorspace_settings.name='sRGB'if 'basecolor'in path.name or 'preview'in path.name else'Non-Color';arr=np.array(im.pixels[:],np.float32).reshape(im.size[1],im.size[0],4);source=arr.copy()
 for p in patches:
  x,y,w,h=p['rect']
  for ix in range(int(x),int(np.ceil(x+w))):
   t=np.clip((ix-x)/w,0,1);uv=np.array(p['uv_a'])*(1-t)+np.array(p['uv_b'])*t;col=source[int(np.clip(uv[1]*1024,0,1023)),int(np.clip(uv[0]*1024,0,1023))].copy()
   for iy in range(int(y),int(y+h)):
    c=col.copy()
    if 'basecolor'in path.name or 'preview'in path.name:c[:3]*=1-.30*(iy-y)/h
    if 'normal'in path.name:c[:3]=(.5,.5,1)
    arr[1023-iy,ix]=c
 im.pixels.foreach_set(arr.ravel());im.filepath_raw=str(path);im.file_format='PNG';im.save();bpy.data.images.remove(im)
for im in bpy.data.images:
 if im.source=='FILE' and im.filepath and Path(bpy.path.abspath(im.filepath)).is_file():
  try:im.unpack(method='REMOVE');im.reload()
  except RuntimeError:im.reload()
(P/'review/sleeve_root_charts.json').write_text(json.dumps(patches,indent=2));bpy.ops.file.pack_all();print('SLEEVE EXTENSIONS' ,len(created),flush=True);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'))
