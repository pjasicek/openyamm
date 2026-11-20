"""Locate the dedicated head's stray eyebrow fragments and genuine closed components."""
from pathlib import Path
import bpy,bmesh,numpy as np,json,sys
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/head_smart_return.blend'));head=next(o for o in bpy.data.objects if o.type=='MESH')
for o in bpy.data.objects:o.select_set(o is head)
bpy.context.view_layer.objects.active=head;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.separate(type='LOOSE');bpy.ops.object.mode_set(mode='OBJECT')
report=[]
for i,o in enumerate(sorted([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:-len(o.data.vertices))):
 o.name=f'H{i:02}';co=np.array([tuple(v.co) for v in o.data.vertices]);bm=bmesh.new();bm.from_mesh(o.data)
 row={'part':o.name,'vertices':len(o.data.vertices),'triangles':sum(len(f.vertices)-2 for f in o.data.polygons),'lo':co.min(0).tolist(),'hi':co.max(0).tolist(),'boundary':sum(e.is_boundary for e in bm.edges),'nonmanifold':sum(not e.is_manifold and not e.is_boundary for e in bm.edges)}
 report.append(row);bm.free()
 mat=bpy.data.materials.new(o.name);mat.diffuse_color=[(.65,.53,.43,1),(.3,.7,.9,1),(.8,.3,.3,1),(.4,.8,.4,1)][i%4];o.data.materials.append(mat)
(p/'work/head_parts.json').write_text(json.dumps(report,indent=2));print('HEAD_PARTS',json.dumps(report),flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/head_parts.blend'))
common.workbench_clay(bpy.context.scene);common.render_views(str(p/'review/head_parts'),0,1.1,views=('front','left','back'),resolution=(650,650))
