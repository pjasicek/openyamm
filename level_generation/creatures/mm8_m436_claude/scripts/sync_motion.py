from pathlib import Path
import bpy,numpy as np
p=Path(__file__).resolve().parents[1]
def faces_of(me):
 me.calc_loop_triangles();return sorted(min(tuple(t.vertices)[k:]+tuple(t.vertices)[:k] for k in range(3)) for t in me.loop_triangles)
bpy.ops.wm.open_mainfile(filepath=str(p/'work/full_reduced.blend'));body=bpy.data.objects['Body'];bpy.context.view_layer.objects.active=body;tri=body.modifiers.new('Freeze triangles','TRIANGULATE');bpy.ops.object.modifier_move_to_index(modifier=tri.name,index=0);bpy.ops.object.modifier_apply(modifier=tri.name);bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/full_reduced.blend'));co=np.array([tuple(v.co) for v in body.data.vertices]);faces=faces_of(body.data)
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_uv_master.blend'));body=bpy.data.objects['Body'];assert np.allclose(co,np.array([tuple(v.co) for v in body.data.vertices]),atol=1e-8);assert faces==faces_of(body.data)
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
with bpy.data.libraries.load(str(p/'work/full_reduced.blend'),link=False) as (src,dst):dst.actions=src.actions
assert {a.name for a in bpy.data.actions}=={'Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget'}
for a in bpy.data.actions:a.use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_uv_master.blend'))
