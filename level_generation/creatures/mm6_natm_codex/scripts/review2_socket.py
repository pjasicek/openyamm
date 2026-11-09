"""Place the existing launch socket on the measured front surface of the casting palm."""
import bpy,sys,json,runpy
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_lod0.blend'));C.reset()
r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];hand=r.data.bones['B_L_Hand']
normal=(hand.matrix_local.to_3x3()@Vector(json.loads((P/'gates.json').read_text())['hands']['L']['palm_axis'])).normalized()
knuckles=sum((r.data.bones[f'B_L_Finger{i}'].head_local for i in range(1,5)),Vector())/4
center=hand.head_local.lerp(knuckles,.55)
mask=[sum(g.weight for g in v.groups if body.vertex_groups[g.group].name.startswith(('B_L_Hand','B_L_Finger')))>.5 for v in body.data.vertices]
body.data.calc_loop_triangles();faces=[list(t.vertices)for t in body.data.loop_triangles if all(mask[i]for i in t.vertices)]
tree=BVHTree.FromPolygons([v.co for v in body.data.vertices],faces,all_triangles=True)
hit=tree.ray_cast(center+normal*.20,-normal,.40);assert hit[0] is not None
point=hit[0]+normal*.0008;local=hand.matrix_local.inverted()@point
before=r.data.bones['Socket_LeftPalm'].head_local.copy()
receipt={'method':'Ray from outside the anatomical palm normal onto the hand surface, 55% wrist-to-knuckle span; socket sits 0.8 mm above skin.',
         'before_rest_m':list(before),'after_rest_m':list(point),'hand_local_m':list(local),
         'displacement_mm':(point-before).length*1000,'palm_triangle':faces[hit[2]]}
assert (point-center).length<.06
for level in range(4):
    file=P/f'work/runtime_lod{level}.blend';bpy.ops.wm.open_mainfile(filepath=str(file));C.reset();r=bpy.data.objects['Rig']
    bpy.ops.object.select_all(action='DESELECT');r.select_set(True);bpy.context.view_layer.objects.active=r
    bpy.ops.object.mode_set(mode='EDIT');b=r.data.edit_bones['Socket_LeftPalm'];target=r.data.edit_bones['B_L_Hand'].matrix@local;delta=target-b.head;b.head+=delta;b.tail+=delta;bpy.ops.object.mode_set(mode='OBJECT')
    r.location=(0,0,0);bpy.ops.wm.save_as_mainfile(filepath=str(file))
    if level==0:bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_natm.blend'))
(P/'review/round2_socket.json').write_text(json.dumps(receipt,indent=2)+'\n')
runpy.run_path(str(P/'scripts/quick_export.py'),run_name='__main__')
