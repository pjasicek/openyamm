"""Reproject only changed torso triangles with the existing per-piece texture baker."""
import bpy,json,numpy as np,sys,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));from project_open_boundaries import complete,pixels
sel=json.loads((P/'review/reduction/selection.json').read_text());report=[]
def signature(me,f):return tuple(sorted(tuple(round(x,6)for x in me.vertices[i].co)for i in f.vertices))
for entry in sel['body']:
 path=P/entry['blend'];folder=P/entry['textures'];bpy.ops.wm.open_mainfile(filepath=str(path));o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];r.animation_data.action=None
 for b in r.pose.bones:b.matrix_basis.identity()
 with bpy.data.libraries.load(str(P/'work/review1'/(path.stem+'_socket_first.blend')),link=False)as(src,dst):dst.objects=['Body']
 hi=dst.objects[0];bpy.context.scene.collection.objects.link(hi);old={signature(hi.data,f)for f in hi.data.polygons};part=[x.value for x in o.data.attributes['piece'].data]
 changed=[f for f in o.data.polygons if all(part[i]==1 for i in f.vertices)and signature(o.data,f)not in old];assert changed
 im,cov=pixels(folder/'0_uv_coverage.png');hitim,hit=pixels(folder/'0_coverage.png');occupied=cov[:,:,0]>.5;N=len(occupied);patches=[]
 for f in changed:
  assert len(f.vertices)==3
  found=None
  for size in [24,20,16,12]:
   for y in range(2,N-size-2,2):
    for x in range(2,N-size-2,2):
     if not occupied[y-2:y+size+2,x-2:x+size+2].any():found=(x,y,size);break
    if found:break
   if found:break
  assert found,'No free texture patch'
  x,y,size=found;occupied[y-2:y+size+2,x-2:x+size+2]=True;coords=[(x+.5,y+.5),(x+size-.5,y+.5),(x+.5,y+size-.5)]
  for li,coord in zip(f.loop_indices,coords):o.data.uv_layers.active.data[li].uv=np.array(coord)/N
  for iy in range(y,y+size):
   for ix in range(x,x+size):
    if (ix-x)+(iy-y)<=size-1:cov[iy,ix,:3]=1;hit[iy,ix,:3]=0
  patches.append([x,y,size])
 for image,data in [(im,cov),(hitim,hit)]:image.pixels.foreach_set(data.ravel());image.file_format='PNG';image.save();bpy.data.images.remove(image)
 source=[]
 for mi,mat in enumerate(hi.data.materials):
  maps={}
  for key in ['basecolor','region_mask','metal_rough','material_classes']:
   image=bpy.data.images.load(str(folder/f'{mi}_{key}.png'),check_existing=False);image.colorspace_settings.name='sRGB'if key=='basecolor'else'Non-Color';maps[key]=image
  source.append(maps)
 complete(o,hi,source,folder)
 subprocess.run(['/usr/bin/python3',str(P/'scripts/pad_rebake.py'),str(folder),'2'],check=True)
 bpy.data.objects.remove(hi,do_unlink=True)
 for image in bpy.data.images:
  if image.source=='FILE' and image.filepath and Path(bpy.path.abspath(image.filepath)).is_file():
   if image.packed_file:image.unpack(method='REMOVE')
   image.reload()
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(path));report.append({'file':entry['blend'],'rebaked_torso_triangles':len(changed),'patches':patches})
(P/'review/review1_local_rebake.json').write_text(json.dumps(report,indent=2))
