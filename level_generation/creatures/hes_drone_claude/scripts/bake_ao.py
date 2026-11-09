"""AO bake of HDR in its rest pose, without the tier gear and the thrust glow, (work/gear_v1.blend) with claude_shared/bake_creature_ao.py -> textures/hdr_ao_2k.png"""
import bpy, os, sys, runpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'gear_v1.blend'))
# no tier gear and no thrust glow in the shared AO (they exist on one tier only / are a glow card)
import bmesh
bpy.data.objects.remove(bpy.data.objects['HDR_Thrust'], do_unlink=True)
me = bpy.data.objects['HDR'].data; bm = bmesh.new(); bm.from_mesh(me)
pl = bm.faces.layers.int.get('part')
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[pl] >= 5], context='FACES'); bm.to_mesh(me); bm.free()
os.makedirs(os.path.join(HERE, 'textures'), exist_ok=True)
sys.argv = ['blender', '--', 'HDR', os.path.join(HERE, 'textures', 'hdr_ao_2k.png'), '0.04', '2048']
runpy.run_path(os.path.join(os.path.dirname(HERE), 'claude_shared', 'bake_creature_ao.py'), run_name='__main__')
print('AO baked')
