"""Front-view (party's view, along +Y) silhouette of every 4th Standing frame: per frame the posed triangles
projected to (x, z) -> work/front_area.npz (rasterised by front_area_px.py)."""
import bpy, os, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim.blend'))
rig = bpy.data.objects['Feet_Rig']; mesh = bpy.data.objects['Feet']
act = bpy.data.actions['Standing']; rig.animation_data.action = act
if len(getattr(act, 'slots', [])): rig.animation_data.action_slot = act.slots[0]
tris = np.array([p.vertices[:] for p in mesh.data.polygons])
out = []
for f in range(0, 60, 4):
    bpy.context.scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get(); ev = mesh.evaluated_get(dg); me = ev.to_mesh()
    co = np.array([v.co[:] for v in me.vertices]); ev.to_mesh_clear()
    out.append(co[tris][:, :, [0, 2]])
np.savez(os.path.join(HERE, 'work', 'front_area.npz'), tris=np.array(out))
print('FRONT frames', len(out))
