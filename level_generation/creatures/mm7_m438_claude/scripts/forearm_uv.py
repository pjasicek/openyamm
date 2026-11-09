"""Severed-forearm prop UVs (Blender). Mode 'dump': work/props.blend's ForearmMesh (built by make_forearm.py from the
textured master, so it carries the body set's UVMap) gets its own compact layout 'PropUV' (Smart UV Project 66 deg,
the cap included) and the per-triangle old (body atlas) and new UVs plus the cap flag are written to
work/forearm_uv.npz for forearm_textures.py. Mode 'apply': PropUV becomes the only layer 'UVMap'.
Args: -- dump|apply"""
import bpy, sys, os, math
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mode = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'props.blend'))
ob = bpy.data.objects['ForearmMesh']; me = ob.data
if mode == 'dump':
    for l in [l.name for l in me.uv_layers if l.name not in ('UVMap',)]:
        me.uv_layers.remove(me.uv_layers[l])
    if 'PropUV' not in me.uv_layers:
        me.uv_layers.new(name='PropUV')
    me.uv_layers.active = me.uv_layers['PropUV']
    for o in bpy.data.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')
    cap = np.zeros(len(me.polygons), bool); me.attributes['cap'].data.foreach_get('value', cap)
    bone = np.zeros(len(me.polygons), bool)
    if 'bonepart' in me.attributes:
        me.attributes['bonepart'].data.foreach_get('value', bone)
    old, new, cf, bf = [], [], [], []
    for p in me.polygons:
        assert len(p.loop_indices) == 3
        old.append([tuple(me.uv_layers['UVMap'].data[li].uv) for li in p.loop_indices])
        new.append([tuple(me.uv_layers['PropUV'].data[li].uv) for li in p.loop_indices])
        cf.append(cap[p.index]); bf.append(bone[p.index])
    np.savez(os.path.join(HERE, 'work', 'forearm_uv.npz'), old=np.array(old), new=np.array(new), cap=np.array(cf), bone=np.array(bf))
    print('PROPUV triangles', len(old), 'cap', int(np.sum(cf)))
else:
    me.uv_layers.remove(me.uv_layers['UVMap'])
    me.uv_layers['PropUV'].name = 'UVMap'
    print('PROPUV applied')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'props.blend'))
