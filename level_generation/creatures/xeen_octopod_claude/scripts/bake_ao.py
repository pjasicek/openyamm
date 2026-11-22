"""Bake the rest-pose AO (claude_shared/bake_creature_ao.py, reach 4 cm, 2K) of the octopod body (the foam ring
removed first: its UVs overlap the body atlas and it would shade the head's base) from work/anim_v1.blend into
textures/octopod_ao_2k.png. The blend is not saved."""
import bpy, bmesh, os, sys, runpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
rig = bpy.data.objects['Octopod_Rig']; rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
ob = bpy.data.objects['Octopod']
bm = bmesh.new(); bm.from_mesh(ob.data)
lay = bm.faces.layers.int.get('part')
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[lay] == 3], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(ob.data); bm.free()
while len(ob.data.materials) > 1:
    ob.data.materials.pop(index=1)
sys.argv = ['blender', '--', 'Octopod', os.path.join(HERE, 'textures', 'octopod_ao_2k.png'), '0.04', '2048']
runpy.run_path(os.path.join(os.path.dirname(HERE), 'claude_shared', 'bake_creature_ao.py'), run_name='__main__')
print('AO baked')
