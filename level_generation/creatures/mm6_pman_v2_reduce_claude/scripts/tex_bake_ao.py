"""AO per texture set (claude_shared/bake_creature_ao.py, 3 cm, 1024): work/ao_body.png (UVMap, non-head faces),
work/ao_head.png (HeadUV, head faces); the other set's faces are removed so the overlapping layouts do not mix."""
import bpy, bmesh, os, sys, runpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'master_r45.blend'))
original = bpy.data.objects['Body']; parts = []
for layer, name, head in [('UVMap', 'body', 0), ('HeadUV', 'head', 1)]:
    mesh = original.copy(); mesh.data = original.data.copy(); bpy.context.scene.collection.objects.link(mesh); mesh.name = 'AO_' + name
    bm = bmesh.new(); bm.from_mesh(mesh.data); hl = bm.faces.layers.int['head']
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[hl] != head], context='FACES'); bm.to_mesh(mesh.data); bm.free()
    mesh.data.uv_layers.active = mesh.data.uv_layers[layer]; mesh.data.uv_layers[layer].active_render = True
    parts.append((mesh, name))
bpy.data.objects.remove(original, do_unlink=True)
for mesh, name in parts:
    sys.argv = ['bake_ao', '--', mesh.name, os.path.join(HERE, 'work', f'ao_{name}.png'), '.03', '1024']
    runpy.run_path(os.path.join(ROOT, 'level_generation/creatures/claude_shared/bake_creature_ao.py'), run_name='__main__')
