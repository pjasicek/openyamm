"""Project the original connected head onto the aligned HD sculpture; retain the original neck."""
from pathlib import Path
import bpy,bmesh,sys,json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v1_parts.blend'))
old_parts=json.loads((p/'work/st_v1_parts.json').read_text())
remove=[r['name'] for r in old_parts if r['name']!='P00' and r['lo'][2]>1.34 and r['lo'][0]>-.25 and r['hi'][0]<.24 and r['hi'][1]<.06]
for n in remove:bpy.data.objects.remove(bpy.data.objects[n],do_unlink=True)
with bpy.data.libraries.load(str(p/'work/head_v1_parts.blend'),link=False) as (src,dst):dst.objects=[n for n in src.objects if n.startswith('H')]
for o in dst.objects:
 bpy.context.scene.collection.objects.link(o)
 for v in o.data.vertices:v.co+=Vector((-.0035,.04,-.014))
target=bpy.data.objects['H00'];bm=bmesh.new();bm.from_mesh(target.data);tree=BVHTree.FromBMesh(bm);bm.free()
body=bpy.data.objects['P00'];bm=bmesh.new();bm.from_mesh(body.data)
def head(v):return v.co.z>1.42 and abs(v.co.x+.03)<.175 and v.co.y<-.12
edges=[e for e in bm.edges if all(head(v) for v in e.verts)]
bmesh.ops.subdivide_edges(bm,edges=edges,cuts=1,use_grid_fill=True)
changed=0;maxmove=0
for v in bm.verts:
 if not head(v):continue
 hit=tree.find_nearest(v.co)
 if hit[0] is None:continue
 blend=min(1,max(0,(v.co.z-1.42)/.035))*min(1,max(0,(-v.co.y-.12)/.08));dist=(hit[0]-v.co).length
 assert dist*blend<.08, (tuple(v.co),dist,blend)
 v.co=v.co.lerp(hit[0],blend);changed+=1;maxmove=max(maxmove,dist*blend)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free()
hair=[];details=[]
for o in list(dst.objects):
 if o is None:continue
 co=np.array([tuple(v.co) for v in o.data.vertices]);name=o.name
 keep=name in ['H01','H02','H03','H04'] or (co[:,2].max()>1.47 and co[:,2].mean()>1.40 and np.max(np.abs(co[:,0]+.0335))<.245)
 if name=='H00' or not keep:bpy.data.objects.remove(o,do_unlink=True);continue
 if name in ['H01','H02','H03','H04']:details.append(o)
 else:hair.append(o)
for o in bpy.data.objects:o.select_set(o in hair)
bpy.context.view_layer.objects.active=hair[0];bpy.ops.object.join();bpy.context.object.name='P100'
for i,o in enumerate(details):o.name=f'P{101+i}'
# Detached sub-millimetre strips at the toe are generation debris, not an extra digit.
for r in old_parts:
 if r['hi'][2]<.025 and r['tris']<10:
  o=bpy.data.objects.get(r['name'])
  if o:bpy.data.objects.remove(o,do_unlink=True)
for o in bpy.data.objects:
 if o.type=='MESH':
  o.data.materials.clear();mat=bpy.data.materials.get('Clay') or bpy.data.materials.new('Clay');mat.diffuse_color=(.58,.58,.58,1);o.data.materials.append(mat)
  for f in o.data.polygons:f.use_smooth=True
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/anatomy_v2_parts.blend'))
common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/anatomy_v2'),.85,2.1,views=('front','left','back','three_quarter'),resolution=(800,900))
common.render_views(str(p/'review/anatomy_v2_head'),1.51,.52,views=('front','left','three_quarter'),resolution=(700,700),target=(-.03,-.24))
(p/'work/anatomy_v2_report.json').write_text(json.dumps({'method':'head-local subdivision and projection onto aligned HD sculpture, connected original neck retained','head_vertices_projected':changed,'maximum_displacement_m':maxmove,'old_head_shells_replaced':remove,'hair_shells':len(hair),'head_alignment_translation':[-.0035,.04,-.014]},indent=2)+'\n')
print('HEAD_PROJECT',changed,maxmove,len(hair))
