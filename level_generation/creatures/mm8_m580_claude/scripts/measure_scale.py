from pathlib import Path
import bpy,json,numpy as np
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm8_m580.blend'));s=bpy.context.scene;s.render.fps=48;rig=bpy.data.objects['Turtle_Rig'];rig.animation_data.action=bpy.data.actions['SwimIdle'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];m=bpy.data.objects['Turtle'];frames=[]
for i in range(8):
 s.frame_set(i*6);e=m.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=e.to_mesh();mesh.calc_loop_triangles();frames.append(np.array([v.co[:] for v in mesh.vertices]));tri=np.array([t.vertices[:] for t in mesh.loop_triangles]);e.to_mesh_clear()
np.savez(P/'work/scale_samples.npz',co=np.array(frames),tri=tri)
