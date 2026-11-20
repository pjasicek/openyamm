"""Clay views of an npz mesh (MM9 glTF frame), coloured by vertex array `key` if given. Args: <npz> <out prefix> [key] [mirror] . Env VIEWS, ORTHO, CENTER."""
import bpy, sys, os, colorsys
import numpy as np
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]
D=np.load(a[0]); co,tri=D['co'].astype(float),D['tri']
key=a[2] if len(a)>2 and a[2]!='-' else None
lab=D[key] if key else np.zeros(len(co),int)
if len(a)>3:
    n=len(co); co=np.vstack([co,co*[-1,1,1]]); tri=np.vstack([tri,tri[:,[0,2,1]]+n]); lab=np.r_[lab,lab]
bpy.ops.wm.read_factory_settings(use_empty=True)
b=np.c_[co[:,0],-co[:,2],co[:,1]]
me=bpy.data.meshes.new('m'); ob=bpy.data.objects.new('m',me); bpy.context.collection.objects.link(ob)
me.from_pydata(b.tolist(),[],tri.tolist()); me.update()
for p in me.polygons: p.use_smooth=True
sc=bpy.context.scene
col=me.color_attributes.new('c','FLOAT_COLOR','POINT')
u=np.unique(lab); m={x:i for i,x in enumerate(u)}
for i,x in enumerate(lab):
    r,g,bb=colorsys.hsv_to_rgb((m[x]*0.381)%1,.55 if key else 0,.85 if key else .75); col.data[i].color=(r,g,bb,1)
sc.render.engine='BLENDER_WORKBENCH'; sh=sc.display.shading; sh.light='STUDIO'; sh.color_type='VERTEX'; sh.show_cavity=True; sh.show_backface_culling=bool(os.environ.get('CULL'))
sc.render.resolution_x=int(os.environ.get('W',800)); sc.render.resolution_y=int(os.environ.get('H',900))
sc.world=bpy.data.worlds.new('W'); sc.world.color=(.2,.2,.23)
cd=bpy.data.cameras.new('C'); cd.type='ORTHO'; cd.ortho_scale=float(os.environ.get('ORTHO',2.2)); cam=bpy.data.objects.new('C',cd); sc.collection.objects.link(cam); sc.camera=cam
c=Vector([float(x) for x in os.environ.get('CENTER','0,0,0').split(',')]) ; c=Vector((c[0],-c[2],c[1]))
V={'front':(0,-1,0),'left':(1,0,0),'back':(0,1,0),'right':(-1,0,0),'q34':(-1,-1.2,.35),'q34b':(1,1.2,.35),'below':(.2,-.5,-1),'top':(.01,-.2,1)}
for n in os.environ.get('VIEWS','front,left,back,q34').split(','):
    d=Vector(V[n]).normalized(); cam.location=c+d*12; cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f'{a[1]}_{n}.png'; bpy.ops.render.render(write_still=True)
print('VIEWS done')
