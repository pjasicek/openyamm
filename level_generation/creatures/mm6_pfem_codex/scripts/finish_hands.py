import bpy,bmesh,sys,runpy,json,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/step1.blend'));me=bpy.data.objects['Body'].data
bm=bmesh.new();bm.from_mesh(me);pv=bm.verts.layers.int['piece']
for v in bm.verts:
 if v[pv] not in (3,4):continue
 z=v.co.z
 if z<.87 or z>.948:continue
 f=max(0,min(1,(z-.87)/.017))*max(0,min(1,(.948-z)/.016))
 if v.co.y>-.034:v.co.y+=(-.034-v.co.y)*f
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
me.attributes['orig_co'].data.foreach_set('vector',np.array([tuple(v.co) for v in me.vertices]).ravel())
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
common.workbench_clay(bpy.context.scene)
# Isolate each hand for palm and back views.
for side,part,x in [('R',3,-.465),('L',4,.462)]:
 ob=bpy.data.objects['Body'];ob.hide_render=True
 mesh=ob.data.copy();temp=bpy.data.objects.new('HandOnly',mesh);bpy.context.collection.objects.link(temp)
 bm=bmesh.new();bm.from_mesh(mesh);layer=bm.verts.layers.int['piece']
 bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]!=part],context='VERTS');bm.to_mesh(mesh);bm.free()
 common.render_views(str(p/f'review/hand_clean_{side}'),.891,.20,views=('left','right'),resolution=(600,600),target=(x,-.056))
 bpy.data.objects.remove(temp,do_unlink=True);ob.hide_render=False
sys.argv=['arm_rings.py','--',str(p/'work/step1.blend')]
runpy.run_path(str(p/'scripts/arm_rings.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/build_rig.py'),run_name='__main__')
sys.argv=['fit_fingers.py','--',str(p/'work/rig_v1.blend')]
runpy.run_path(str(p/'scripts/fit_fingers.py'),run_name='__main__')
