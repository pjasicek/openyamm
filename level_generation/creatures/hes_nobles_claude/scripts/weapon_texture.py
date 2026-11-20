"""Texture a prepared weapon (work/weapons/<name>.blend) from its registered paint atlas (register_paint.py): front-facing
faces (normal -Y) take the front view, the others the back view (mirrored), as orthographic projections in the guide
frame (work/weapons/<name>_frame.json). Faces whose painted colour is the saturated orange of the energy parts move to
the glow material NB_WeaponGlow (emission by factor only; no emissive texture), the rest to NB_Weapon_<name>
(base colour atlas, roughness 0.45, metallic 0). Optional `thicken` in weapons.json ([z0, z1, factor, centre x]: the grip widened radially). Optional target triangle count (collapse decimation before the UVs). Saves the blend in place.
Args: -- <name> [target triangles]"""
import bpy, sys, os, json, colorsys
import numpy as np
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
name = sys.argv[sys.argv.index('--') + 1:][0]
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, 'work', 'weapons', f'{name}.blend'))
ob = bpy.data.objects['W_' + name]; me = ob.data
TARGET = int(sys.argv[sys.argv.index('--') + 1:][1]) if len(sys.argv[sys.argv.index('--') + 1:]) > 1 else 0
tris = sum(len(p.vertices) - 2 for p in me.polygons)
if TARGET and tris > TARGET * 1.05:                     # the planar UVs come from positions, so reduce first
    bpy.context.view_layer.objects.active = ob
    md = ob.modifiers.new('D', 'DECIMATE'); md.ratio = TARGET / tris; md.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier='D')
TH = json.load(open(os.path.join(P, 'scripts', 'weapons.json'))).get(name, {}).get('thicken')
if TH:                                                    # a handle thinner than the fitted fist: widen it radially
    z0, z1, k, cx = TH
    for v in me.vertices:
        if z0 - 0.02 < v.co.z < z1 + 0.02:
            e = min(1.0, max(0.0, min(v.co.z - (z0 - 0.02), (z1 + 0.02) - v.co.z) / 0.02))
            f = 1 + (k - 1) * e
            v.co.x = cx + (v.co.x - cx) * f; v.co.y *= f
    me.update()
fr = json.load(open(os.path.join(P, 'work', 'weapons', f'{name}_frame.json'))); S = fr['size']
img = bpy.data.images.load(os.path.join(P, 'textures', 'weapons', f'{name}_basecolor.png'), check_existing=True)
W, H = img.size; px = np.array(img.pixels[:]).reshape(H, W, 4)[..., :3]
for l in list(me.uv_layers): me.uv_layers.remove(l)
uv = me.uv_layers.new(name='UVMap').data
glow = []
for p in me.polygons:
    front = p.normal.y < 0
    for li in p.loop_indices:
        co = me.vertices[me.loops[li].vertex_index].co
        u = (co.x / S + 0.5) if front else (-co.x / S + 0.5)
        uv[li].uv = ((u * 0.5) + (0.0 if front else 0.5), co.z / S + 0.5)
    c = p.center; u = (c.x / S + 0.5) if front else (-c.x / S + 0.5)
    x = int(np.clip(((u * 0.5) + (0.0 if front else 0.5)) * W, 0, W - 1)); y = int(np.clip((c.z / S + 0.5) * H, 0, H - 1))
    r, g, b = px[y, x]; h, s, v = colorsys.rgb_to_hsv(r, g, b)
    glow.append(0.03 < h < 0.12 and s > 0.75 and v > 0.85)


def material(mname, colour_image=None, emit=None):
    m = bpy.data.materials.get(mname) or bpy.data.materials.new(mname); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type not in ('OUTPUT_MATERIAL', 'BSDF_PRINCIPLED'): nt.nodes.remove(n)
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Metallic'].default_value = 0.0; b.inputs['Roughness'].default_value = 0.45
    if colour_image:
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = colour_image; nt.links.new(t.outputs[0], b.inputs['Base Color'])
    if emit:
        b.inputs['Base Color'].default_value = (*emit, 1); b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = 1.0
    return m


me.materials.clear()
me.materials.append(material(f'NB_Weapon_{name}', img))
me.materials.append(material('NB_WeaponGlow', emit=(1.0, 0.42, 0.08)))
for p, gl in zip(me.polygons, glow): p.material_index = 1 if gl else 0
for p in me.polygons: p.use_smooth = True
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(P, 'work', 'weapons', f'{name}.blend'))
print('WEAPONTEX', name, 'glow faces', sum(glow), 'of', len(glow)); sys.stdout.flush(); os._exit(0)
