"""Textured static export for clips_mm9.py: materials Colloidal (body set), ColloidalHead on PartUV (colloidal warrior, from mm9_bigfoot_claude); the armature lifted so model y = 0 is the floor.
Args: <uv blend> <out glb>. Textures by the fixed names in textures/."""
import bpy, bmesh, sys, os
import numpy as np
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
TX = bpy.path.abspath('//../textures')
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data: rig.animation_data.action = None
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
for b in rig.pose.bones: b.matrix_basis.identity()
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not body: bpy.data.objects.remove(o)
# stray shards left by the reductions
bm = bmesh.new(); bm.from_mesh(me)
seen = set(); dead = []
for f0 in bm.faces:
    if f0 in seen: continue
    st = [f0]; seen.add(f0); cc = [f0]
    while st:
        f = st.pop()
        for e in f.edges:
            for g in e.link_faces:
                if g not in seen: seen.add(g); st.append(g); cc.append(g)
    if len(cc) < 5: dead += cc
bmesh.ops.delete(bm, geom=dead, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
print('SHARDS', len(dead))
# the zipped wrist faces and the neck bridge take the skin's winding (a hole showed in the wrap)
pl = bm.verts.layers.int['part']
skin = [f for f in bm.faces if all(v[pl] == 0 for v in f.verts)]
before = sum(1 for f in skin if f.normal.length > 0)
bm.normal_update()
bmesh.ops.recalc_face_normals(bm, faces=skin)
print('SHARDS skin faces', len(skin))
bm.to_mesh(me); bm.free()
pu, bu = me.uv_layers['PartUV'].data, me.uv_layers['UVMap'].data
for i in range(len(me.loops)): bu[i].uv = pu[i].uv
me.uv_layers.active = me.uv_layers['UVMap']
me.uv_layers.remove(me.uv_layers['HeadUV']); me.uv_layers.remove(me.uv_layers['PartUV'])
def material(name, base, normal, mr):
    mat = bpy.data.materials.new(name); mat.use_nodes = True; mat.use_backface_culling = True
    nt = mat.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    def tex(fname, cs):
        img = bpy.data.images.load(os.path.join(TX, fname), check_existing=True); img.colorspace_settings.name = cs
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; return n
    nt.links.new(tex(base, 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
    nmap = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex(normal, 'Non-Color').outputs['Color'], nmap.inputs['Color'])
    nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tex(mr, 'Non-Color').outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return mat
me.materials.clear()
me.materials.append(material('Colloidal', 'cw_body_final.png', 'cw_body_normal.png', 'cw_body_orm.png'))
me.materials.append(material('ColloidalHead', 'cw_head_final.png', 'cw_head_normal.png', 'cw_head_orm.png'))
mat = np.zeros(len(me.polygons), np.int32); me.attributes['mat'].data.foreach_get('value', mat)
me.polygons.foreach_set('material_index', (mat // 2).tolist())
for a in [a.name for a in me.attributes if a.name in ('part', 'mat', 'fpart', 'hand', 'graft_s', 'graft_side')]:
    me.attributes.remove(me.attributes[a])
bpy.context.view_layer.objects.active = body
for o in bpy.data.objects: o.select_set(o == body)
bpy.ops.object.shade_smooth()
lift = -min((body.matrix_world @ v.co).z for v in me.vertices)
rig.location.z += lift
bpy.context.view_layer.update()
print('LIFT', round(lift, 4))
body.name = 'Colloidal'; me.name = 'Colloidal'
for o in bpy.data.objects: o.select_set(o in (body, rig))
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_animations=False, export_skins=True, export_yup=True, export_image_format='AUTO', export_attributes=False)
print('EXPORTED', OUT, len(me.polygons))
