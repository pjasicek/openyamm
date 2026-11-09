import bpy,sys,numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_settled.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];s=bpy.data.objects['StaffMesh'];sc=bpy.context.scene
r.animation_data.action=bpy.data.actions['Running'];r.animation_data.action_slot=r.animation_data.action.slots[0]
def coords(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();a=np.array([(o.matrix_world@v.co)[:] for v in me.vertices]);ev.to_mesh_clear();return a
parts=np.array([a.value for a in b.data.attributes['piece'].data]);faces=[list(f.vertices) for f in b.data.polygons if int(parts[f.vertices[0]])==0];sf=[list(f.vertices) for f in s.data.polygons]
common.workbench_clay(sc)
for f in [20,20.25,20.5,20.75,21]:
 sc.frame_set(int(f),subframe=f%1);bc,st=coords(b),coords(s);pairs=BVHTree.FromPolygons(bc.tolist(),faces).overlap(BVHTree.FromPolygons(st.tolist(),sf))
 print('FRAME',f,'staffbbox',st.min(0),st.max(0),'hand',tuple((r.matrix_world@r.pose.bones['B_R_Hand'].matrix).translation),'hits',len(pairs))
 if pairs:print('HITCENTRES',np.mean([bc[faces[i]].mean(0) for i,j in pairs],0))
 common.render_views(str(P/'review'/f'running_{f}'),.85,2.1,views=('front','right'),resolution=(400,800))
