"""Project-local entry for ../claude_shared/bake_creature_ao.py: args <blend> <mesh> <out.png> [reach] [size].
SEPARATE_ATTR=<int face attribute> (env): faces with that attribute = 1 (the grafted head, which has its own UVs and
texture set) are split off into their own object first, so they still occlude but are not baked into the atlas."""
import bpy, sys, os, runpy
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
attr = os.environ.get('SEPARATE_ATTR')
if attr:
    import bmesh
    ob = bpy.data.objects[argv[1]]
    me = ob.data
    keep = bmesh.new(); keep.from_mesh(me)
    fl = keep.faces.layers.int.get(attr)
    if fl is not None:
        other = keep.copy()
        ofl = other.faces.layers.int.get(attr)
        bmesh.ops.delete(keep, geom=[f for f in keep.faces if f[fl] == 1], context='FACES')
        bmesh.ops.delete(other, geom=[f for f in other.faces if f[ofl] != 1], context='FACES')
        keep.to_mesh(me)
        om = bpy.data.meshes.new(argv[1] + '_occluder'); other.to_mesh(om)
        oo = bpy.data.objects.new(argv[1] + '_occluder', om)
        bpy.context.scene.collection.objects.link(oo)
        oo.matrix_world = ob.matrix_world
        for md in ob.modifiers:
            if md.type == 'ARMATURE':
                m2 = oo.modifiers.new(md.name, 'ARMATURE'); m2.object = md.object
                for g in ob.vertex_groups:
                    oo.vertex_groups.new(name=g.name)
    keep.free()
sys.argv = ['blender', '--'] + argv[1:]
runpy.run_path(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                            'claude_shared', 'bake_creature_ao.py'), run_name='__main__')
