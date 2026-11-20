"""Fresh UVs for the fixed bat (work/fix_master.blend; one texture set): Smart UV Project as the original
(66 degrees), head islands 2.5x texel density (claude_shared/uv_head_density.py), concave packing; Meshy upload
work/bat_upload.glb. Out: work/uv_master.blend, work/uv_tris.npy (layout check)."""
import os, sys, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'claude_shared')); from uv_head_density import scale_head_islands  # noqa: E402
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'fix_master.blend'))
o = bpy.data.objects['Bat']; rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.004, area_weight=0.0, scale_to_bounds=False)
scale_head_islands(o, ('Head', 'Ear_L', 'Ear_R'), factor=2.5)
bpy.ops.uv.select_all(action='SELECT')
bpy.ops.uv.pack_islands(rotate=True, margin=.003, margin_method='FRACTION', shape_method='CONCAVE')
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'uv_master.blend'))
me = o.data; uv = me.uv_layers.active; me.calc_loop_triangles()
np.save(os.path.join(HERE, 'work', 'uv_tris.npy'), np.array([[0] + [c for li in t.loops for c in uv.data[li].uv] for t in me.loop_triangles], np.float32))
dup = o.copy(); dup.data = me.copy(); dup.parent = None; dup.modifiers.clear(); dup.vertex_groups.clear()
bpy.context.collection.objects.link(dup); dup.data.materials.clear()
m = bpy.data.materials.new('Neutral'); m.use_nodes = True; dup.data.materials.append(m)
bpy.ops.object.select_all(action='DESELECT'); dup.select_set(True); bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'work', 'bat_upload.glb'), use_selection=True, export_format='GLB',
                          export_animations=False, export_skins=False, export_attributes=False, export_morph=False)
print('UV', len(me.loop_triangles), 'triangles')
