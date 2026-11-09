"""Head and neck close-ups of a runtime GLB (face defect checks: eyes, lips, neck seam).

Args: -- <glb> <out png> <clip:frame48[,clip:frame48...]> [views: front,rside,lside,q34,eyes,mouth,neckR,neckL]
Views are framed relative to the head bone; eyes/mouth/neck* are tight close-ups (ortho 0.12).
`bind` as the clip renders the rest pose. One row per item, one column per view; EEVEE with the GLB's own maps
(normal map included), camera framed on the head bone. Writes <out png>.list for sheet_frames.py <out png>."""
import bpy, bmesh, sys, os, math
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, out, items = a[0], a[1], a[2].split(',')
views = (a[3] if len(a) > 3 else 'front,rside,lside,q34').split(',')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name):
        o.hide_render = True
sc = bpy.context.scene
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = sc.render.resolution_y = 360
sc.world = bpy.data.worlds.new('W'); sc.world.use_nodes = True
bg = next(n for n in sc.world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.35, 0.37, 0.4, 1); bg.inputs['Strength'].default_value = 1.0
for nm, rot, en in (('key', (50, 0, -30), 3.0), ('fill', (60, 0, 140), 1.2)):
    ld = bpy.data.lights.new(nm, 'SUN'); ld.energy = en
    if os.environ.get('NOSHADOW'):
        ld.use_shadow = False
    lo = bpy.data.objects.new(nm, ld); sc.collection.objects.link(lo)
    lo.rotation_euler = [math.radians(x) for x in rot]
if os.environ.get('UVMODE'):      # mm9_bjarni: render head-set UVs as colour (R=u, G=v, B=1 head material) to locate texels
    sc.view_settings.view_transform = 'Raw'; sc.render.image_settings.color_depth = '16'
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        for slot in o.material_slots:
            m = slot.material.copy(); slot.material = m; nt = m.node_tree
            for n in list(nt.nodes):
                nt.nodes.remove(n)
            tc = nt.nodes.new('ShaderNodeUVMap'); em = nt.nodes.new('ShaderNodeEmission')
            sep = nt.nodes.new('ShaderNodeSeparateXYZ'); comb = nt.nodes.new('ShaderNodeCombineXYZ')
            nt.links.new(tc.outputs['UV'], sep.inputs[0]); nt.links.new(sep.outputs[0], comb.inputs[0])
            nt.links.new(sep.outputs[1], comb.inputs[1]); comb.inputs[2].default_value = 1.0 if 'Head' in m.name else 0.0
            nt.links.new(comb.outputs[0], em.inputs['Color']); out_n = nt.nodes.new('ShaderNodeOutputMaterial')
            nt.links.new(em.outputs[0], out_n.inputs['Surface'])
if os.environ.get('IDMODE'):      # mm9_bjarni: flat per-triangle id colour (R + 256 G + 65536 B = triangle index + 1, head material only)
    sc.view_settings.view_transform = 'Raw'; sc.render.filter_size = 0.01; sc.render.dither_intensity = 0
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.hide_render:
            continue
        me = o.data
        if not any('Head' in m.name for m in me.materials):
            continue
        bm_ = bmesh.new(); bm_.from_mesh(me); bmesh.ops.triangulate(bm_, faces=bm_.faces[:]); bm_.to_mesh(me); bm_.free()
        at = me.color_attributes.new('fid', 'FLOAT_COLOR', 'CORNER')
        for poly in me.polygons:
            hm = 'Head' in me.materials[poly.material_index].name
            i = poly.index + 1 if hm else 0
            c = ((i % 256) / 255.0, ((i // 256) % 256) / 255.0, (i // 65536) / 255.0, 1.0)
            for li in poly.loop_indices:
                at.data[li].color = c
        for slot in o.material_slots:
            m = slot.material.copy(); slot.material = m; nt = m.node_tree
            for n in list(nt.nodes):
                nt.nodes.remove(n)
            ca = nt.nodes.new('ShaderNodeVertexColor'); ca.layer_name = 'fid'; em = nt.nodes.new('ShaderNodeEmission')
            nt.links.new(ca.outputs['Color'], em.inputs['Color']); out_n = nt.nodes.new('ShaderNodeOutputMaterial')
            nt.links.new(em.outputs[0], out_n.inputs['Surface'])
if os.environ.get('NONORMAL'):     # mm9_bjarni: normal maps disconnected (shading check)
    for m in bpy.data.materials:
        if m.node_tree:
            for n in m.node_tree.nodes:
                if n.type == 'NORMAL_MAP':
                    for l in list(n.outputs[0].links):
                        m.node_tree.links.remove(l)
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.type = 'ORTHO'; cd.ortho_scale = 0.36
hb = next(b for b in rig.pose.bones if b.name.endswith('Head'))
# (camera yaw deg: 0 front, -90 the character's right side; height offset from the head bone m; ortho scale m;
#  optional pitch deg, negative = from below)
VIEWS = {'front': (0, 0.03, 0.3), 'rside': (-90, 0.03, 0.3), 'lside': (90, 0.03, 0.3), 'q34': (35, 0.03, 0.3),
         'back': (180, 0.03, 0.3), 'eyes': (0, 0.1, 0.09), 'mouth': (0, 0.035, 0.09), 'neckR': (-90, 0.0, 0.14),
         'neckL': (90, 0.0, 0.14), 'eyesLow': (10, 0.1, 0.09, -12), 'mouthLow': (-15, 0.035, 0.09, -12),
         'brow': (0, 0.15, 0.12), 'browQ': (35, 0.15, 0.13), 'browQL': (-35, 0.15, 0.13), 'party': (0, 0.06, 0.45, -4)}
rows = []
os.makedirs('/tmp/head_closeups', exist_ok=True)
for it in items:
    clip, f = it.split(':')
    if clip == 'bind':
        if rig.animation_data:
            rig.animation_data.action = None
        for pb in rig.pose.bones:
            pb.matrix_basis.identity()
        sc.frame_set(0)
    else:
        act = bpy.data.actions[clip] if clip in bpy.data.actions else next(x for x in bpy.data.actions
                                                                            if x.name.startswith(clip))
        rig.animation_data_create(); rig.animation_data.action = act
        if getattr(act, 'slots', None) is not None and len(act.slots):
            rig.animation_data.action_slot = act.slots[0]
        t = float(f) / 48.0
        sc.frame_set(int(t * 24.0), subframe=(t * 24.0) % 1.0)
    bpy.context.view_layer.update()
    m = rig.matrix_world @ hb.matrix
    tgt = m.translation - Vector((0, 0, 0.02))
    row = []
    for v in views:
        ang, dz, scale = VIEWS[v][:3]
        r = math.radians(ang); pt = math.radians(VIEWS[v][3] if len(VIEWS[v]) > 3 else 0)
        t = tgt + Vector((0, 0, dz))
        cd.ortho_scale = scale
        cam.location = t + Vector((math.sin(r) * math.cos(pt) * 2, -math.cos(r) * math.cos(pt) * 2, math.sin(pt) * 2))
        cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
        fn = f'/tmp/head_closeups/{os.getpid()}_{len(rows)}_{len(row)}.png'
        sc.render.filepath = fn; bpy.ops.render.render(write_still=True); row.append(fn)
        if os.environ.get('PROBE'):          # PROBE="view:x,y;..." prints the rendered UV at pixels (top-left origin)
            img = bpy.data.images.load(fn); W_, H_ = img.size; px = np.array(img.pixels[:]).reshape(H_, W_, 4)
            for pr in os.environ['PROBE'].split(';'):
                pv, xy = pr.split(':'); x, y = (int(c) for c in xy.split(','))
                if pv == v:
                    print('PROBE', v, x, y, [round(float(c), 4) for c in px[H_ - 1 - y, x, :3]])
                    if os.environ.get('IDMODE'):
                        im2 = bpy.data.images.load(fn, check_existing=False); im2.colorspace_settings.name = 'Non-Color'
                        q_ = np.array(im2.pixels[:]).reshape(H_, W_, 4)[H_ - 1 - y, x, :3]
                        r_, g_, b_ = (int(round(c * 255)) for c in q_); fid = r_ + 256 * g_ + 65536 * b_ - 1
                        hm = next(o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render and 'fid' in o.data.color_attributes)
                        poly = hm.data.polygons[fid]; uvl = hm.data.uv_layers.active.data
                        print('PROBEFACE', v, x, y, fid, [round(c, 3) for c in poly.center],
                              [[round(uvl[li].uv[0] * 2048), round((1 - uvl[li].uv[1]) * 2048)] for li in poly.loop_indices])
    rows.append((it, row))
open(out + '.list', 'w').write('\n'.join(it + '\t' + '\t'.join(r) for it, r in rows))
print('CLOSEUPS', out, len(rows))
