"""Bake the robot AO without the eye lens: the lens slides along the belt in the clips, so its rest-pose occlusion
would leave a dark patch on the belt. Removes the eye faces in memory, then runs claude_shared/bake_creature_ao.py.
Usage: blender --background work/anim_v1.blend --python scripts/bake_ao_no_eye.py -- Robot <out.png> [reach]"""
import bpy, bmesh, os, sys
mesh = bpy.data.objects['Robot']
bm = bmesh.new(); bm.from_mesh(mesh.data)
part = bm.faces.layers.int['part']
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[part] == 3], context='FACES')
bm.to_mesh(mesh.data); bm.free()
script = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                      'claude_shared', 'bake_creature_ao.py')
exec(compile(open(script).read(), script, 'exec'))
