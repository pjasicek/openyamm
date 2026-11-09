"""Rest position of the candidate vertex nearest to a posed point. Usage: blender -b -P rest_of.py -- <cand> <clip> <frame> x,y,z"""
import sys, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath='work/ladder.blend')
c = bpy.data.objects[a[0]]; rig = bpy.data.objects['Rig']; act = bpy.data.actions[a[1]]
rig.animation_data.action = act
if act.slots:
    rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(int(a[2])); P = Vector([float(x) for x in a[3].split(',')])
ev = c.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
best = min(range(len(me.vertices)), key=lambda i: ((c.matrix_world @ me.vertices[i].co) - P).length)
print('REST', [round(x, 3) for x in (c.matrix_world @ c.data.vertices[best].co)], 'posed', [round(x, 3) for x in (c.matrix_world @ me.vertices[best].co)])
