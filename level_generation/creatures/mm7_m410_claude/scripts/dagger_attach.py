"""Review/gate copy of a rig with the modelled dagger skinned 100 % to the keyed 'Dagger' bone (author_dagger.py) as
piece 1000 / garment 9, so g6_prop.py (PROP_HAND=R) and the probes see it. Args: -- <in blend> <out blend>"""
import bpy, sys, os
src, out = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; scene = bpy.context.scene
with bpy.data.libraries.load(os.path.join(HERE, 'work', 'props.blend'), link=False) as (s_, d_):
    d_.objects = ['DaggerMesh']
dg = d_.objects[0]; scene.collection.objects.link(dg)
dg.data.transform(rig.data.bones['Dagger'].matrix_local)
n = len(dg.data.vertices)
dg.vertex_groups.new(name='Dagger').add(list(range(n)), 1.0, 'REPLACE')
for at in ('piece', 'garment', 'finger'):
    if at in body.data.attributes:
        dg.data.attributes.new(at, 'INT', 'POINT').data.foreach_set('value', [1000 if at == 'piece' else (9 if at == 'garment' else 0)] * n)
if 'Dagger' not in body.vertex_groups:
    body.vertex_groups.new(name='Dagger')
for o in bpy.data.objects:
    o.select_set(o in (body, dg))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
print('DAGGERATTACH verts', n)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
