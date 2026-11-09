"""Carry head-set paint from the old head layout (HeadUV_old) to the new one (HeadUV, relayout_head.py): Cycles emission
bake of the re-laid head faces only, at 2x the image size (one resample, supersampled), written to
work/transfer/<name>_bake.png with alpha = baked texels (16 px margin). transfer_head_merge.py pastes it into the
head square of the original image (hands and ear islands keep their own texels).
Args (Blender): <blend> <image png> ... (each a composed head-set map in the old layout)"""
import bpy, bmesh, sys, os
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
body = bpy.data.objects['Body']; rig = body.parent
for b in rig.pose.bones:
    b.matrix_basis.identity()
me = body.data
n = len(me.polygons)
hd = np.zeros(n, np.int32); hn = np.zeros(n, np.int32)
me.attributes['head'].data.foreach_get('value', hd)
me.attributes['hand'].data.foreach_get('value', hn)
eg = body.vertex_groups.get('Bip01 ElfEars')
earv = {v.index for v in me.vertices if eg and any(g.group == eg.index and g.weight > 0.5 for g in v.groups)}
ear = np.array([all(i in earv for i in p.vertices) for p in me.polygons])
head = (hd == 1) & (hn == 0) & ~ear
dup = body.copy(); dup.data = me.copy(); dup.modifiers.clear(); dup.parent = None
dup.matrix_world = body.matrix_world
bpy.context.scene.collection.objects.link(dup)
bm = bmesh.new(); bm.from_mesh(dup.data); bm.faces.ensure_lookup_table()
# needles: degenerate midline slivers whose new UVs run across the face chart (uv_atlas scales a near-zero-area chart
# up) painted streaks from the nose over the cheek; they are invisible (under 0.2 mm2), so they are not baked
uvn = bm.loops.layers.uv['HeadUV']


def needle(f):
    e3 = max((f.verts[i].co - f.verts[(i + 1) % 3].co).length for i in range(3))
    eu = max((f.loops[i][uvn].uv - f.loops[(i + 1) % 3][uvn].uv).length for i in range(3))
    return eu > 0.01 and eu / max(e3, 1e-9) > 8.0      # typical HeadUV density is ~1.5-3 per metre


drop = [f for f in bm.faces if not head[f.index] or needle(f)]
print('XFER needles', sum(1 for f in bm.faces if head[f.index] and needle(f)))
bmesh.ops.delete(bm, geom=drop, context='FACES')
bm.to_mesh(dup.data); bm.free()
dup.vertex_groups.clear()
for o in bpy.data.objects:
    o.hide_render = o is not dup
    o.select_set(o is dup)
bpy.context.view_layer.objects.active = dup
dm = dup.data
dm.uv_layers.active = dm.uv_layers['HeadUV']
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = 4; sc.cycles.device = 'CPU'
sc.render.bake.margin = 16; sc.render.bake.use_clear = True
out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'transfer')
os.makedirs(out_dir, exist_ok=True)
for path in argv[1:]:
    src = bpy.data.images.load(path); src.colorspace_settings.name = 'Non-Color'
    N = src.size[0] * 2
    tgt = bpy.data.images.new('bake', N, N, alpha=True, float_buffer=False)
    tgt.colorspace_settings.name = 'Non-Color'
    mat = bpy.data.materials.new('xfer'); mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()
    uvn = nt.nodes.new('ShaderNodeUVMap'); uvn.uv_map = 'HeadUV_old'
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = src; tex.interpolation = 'Linear'
    em = nt.nodes.new('ShaderNodeEmission'); outn = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(uvn.outputs['UV'], tex.inputs['Vector']); nt.links.new(tex.outputs['Color'], em.inputs['Color'])
    nt.links.new(em.outputs['Emission'], outn.inputs['Surface'])
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = tgt
    nt.nodes.active = tn; tn.select = True
    dm.materials.clear(); dm.materials.append(mat)
    bpy.ops.object.bake(type='EMIT', use_clear=True, margin=16)
    name = os.path.splitext(os.path.basename(path))[0]
    tgt.filepath_raw = os.path.join(out_dir, name + '_bake.png'); tgt.file_format = 'PNG'; tgt.save()
    print('XFER', name, N)
