"""Short-range AO (Cycles CPU, rest pose) for the body (UVMap, 2048) and the head set (HeadUV, 1024, head faces alone with
the rest of the body as occluder). Args: <blend> <body ao png> <head ao png> [reach]"""
import bpy, bmesh, sys
a = sys.argv[sys.argv.index('--') + 1:]
SRC, OUTB, OUTH = a[:3]; REACH = float(a[3]) if len(a) > 3 else 0.04
bpy.ops.wm.open_mainfile(filepath=SRC)
for rig in (o for o in bpy.data.objects if o.type == 'ARMATURE'):
    if rig.animation_data: rig.animation_data.action = None
    for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
body = bpy.data.objects['Body']
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not body: bpy.data.objects.remove(o)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 96
if sc.world is None: sc.world = bpy.data.worlds.new('w')
sc.world.light_settings.distance = REACH
# evaluated rest-pose copy without the armature modifier
dg = bpy.context.evaluated_depsgraph_get()
me = bpy.data.meshes.new_from_object(body.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
bpy.data.objects.remove(body)


def obj(name, keep_head):
    m = me.copy(); bm = bmesh.new(); bm.from_mesh(m)
    hl = bm.faces.layers.int['head']
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if bool(f[hl]) != keep_head], context='FACES') if keep_head is not None else None
    bm.to_mesh(m); bm.free()
    o = bpy.data.objects.new(name, m); sc.collection.objects.link(o)
    return o


def bake(o, uv, size, out):
    img = bpy.data.images.new('ao_' + o.name, size, size, alpha=False)
    mat = bpy.data.materials.new('bake_' + o.name); mat.use_nodes = True
    n = mat.node_tree.nodes.new('ShaderNodeTexImage'); n.image = img; mat.node_tree.nodes.active = n
    o.data.materials.clear(); o.data.materials.append(mat)
    o.data.uv_layers.active = o.data.uv_layers[uv]
    for x in bpy.data.objects: x.select_set(x is o)
    bpy.context.view_layer.objects.active = o
    sc.render.bake.margin = 8
    bpy.ops.object.bake(type='AO')
    img.filepath_raw = out; img.file_format = 'PNG'; img.save()
    print('AO', out)


full = obj('Full', None)
bake(full, 'UVMap', 2048, OUTB)
bpy.data.objects.remove(full)
rest = obj('Rest', False); hd = obj('Head', True)
bake(hd, 'HeadUV', 1024, OUTH)
