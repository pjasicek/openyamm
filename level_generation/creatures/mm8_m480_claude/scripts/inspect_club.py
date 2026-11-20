from pathlib import Path
import bpy,sys,json
import numpy as np
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(p/'meshy/club_v1/model_urls_glb.glb'))
objs=[o for o in bpy.data.objects if o.type=='MESH']
for o in objs:
    o.data.transform(o.matrix_world);o.matrix_world=Matrix.Identity(4)
co=np.array([tuple(v.co) for o in objs for v in o.data.vertices])
print('CLUB BOUNDS',co.min(0),co.max(0))
axis=np.linalg.svd(co-co.mean(0))[2][0]
if axis[2]<0:axis=-axis
turn=Vector(axis).rotation_difference(Vector((0,0,1))).to_matrix()
for o in objs:
    o.data.transform(turn.to_4x4())
co=np.array([tuple(v.co) for o in objs for v in o.data.vertices])
scale=.60/np.ptp(co[:,2]); center=(co.min(0)+co.max(0))/2;center[2]=co[:,2].min()
for o in objs:
    for v in o.data.vertices:v.co=(v.co-Vector(center))*scale
    o.select_set(True)
bpy.context.view_layer.objects.active=objs[0]
bpy.ops.object.join();obj=bpy.context.object;obj.name='Club'
co=np.array([tuple(v.co) for v in obj.data.vertices])
# A genuine exposed shaft section above the lower knuckle; final radius is measured here.
mask=(co[:,2]>.08)&(co[:,2]<.17)
centerxy=np.median(co[mask,:2],axis=0)
for z in np.arange(.06,.20,.02):
    pts=co[np.abs(co[:,2]-z)<.012]
    print('SECTION',z,pts.min(0),pts.max(0))
r=np.linalg.norm(co[mask,:2]-centerxy,axis=1)
record={'length_m':.6,'grip_z':.125,'grip_xy':centerxy.tolist(),'grip_radius_p95':float(np.percentile(r,95)),
        'grip_radius_max':float(r.max()),'triangles':sum(len(x.vertices)-2 for x in obj.data.polygons)}
(p/'work/club_fit.json').write_text(json.dumps(record,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/club.blend'))
common.workbench_clay(bpy.context.scene,textured=True)
common.render_views(str(p/'review/club'),.3,.72,views=('front','left','back'),resolution=(400,650))
print(record)
