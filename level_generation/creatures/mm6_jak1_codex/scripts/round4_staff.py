"""One fixed staff reduction: retain accepted hook; bake raised shaft details into shared maps."""
import bpy, bmesh, json, math, sys
import numpy as np
from pathlib import Path
sys.dont_write_bytecode = True
P = Path(__file__).resolve().parents[1]
R = P / 'review/round4'
W = P / 'work/round4'
T = P / 'textures/round4_staff'
T.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
a = np.load(W / 'accepted_staff.npz')
vertices = a['POSITION']; triangles = a['indices']
mesh = bpy.data.meshes.new('AcceptedStaff')
mesh.from_pydata(vertices.tolist(), [], triangles.tolist()); mesh.update()
uv = mesh.uv_layers.new(name='UVMap')
for face in mesh.polygons:
    face.use_smooth = True
    for loop in face.loop_indices:
        u, v = a['TEXCOORD_0'][mesh.loops[loop].vertex_index]
        uv.data[loop].uv = (u, 1-v)
mesh.normals_split_custom_set([a['NORMAL'][loop.vertex_index] for loop in mesh.loops])
high = bpy.data.objects.new('AcceptedStaff', mesh); bpy.context.collection.objects.link(high)
source = bpy.data.materials.new('AcceptedStaff'); source.use_nodes = True; mesh.materials.append(source)
nt = source.node_tree; bs = nt.nodes.get('Principled BSDF'); output = nt.nodes.get('Material Output')
images = {}
for key in ['basecolor', 'metal_rough', 'normal']:
    image = bpy.data.images.load(str(W / f'accepted_{key}.png'))
    image.colorspace_settings.name = 'sRGB' if key == 'basecolor' else 'Non-Color'
    node = nt.nodes.new('ShaderNodeTexImage'); node.image = image; images[key] = node
nt.links.new(images['basecolor'].outputs['Color'], bs.inputs['Base Color'])
normal = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(images['normal'].outputs['Color'], normal.inputs['Color'])
nt.links.new(normal.outputs['Normal'], bs.inputs['Normal'])
sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(images['metal_rough'].outputs['Color'], sep.inputs[0])
nt.links.new(sep.outputs['Green'], bs.inputs['Roughness']); bs.inputs['Metallic'].default_value = 0
# Coordinates remain in the accepted attachment frame, with grip origin and hook unchanged.
unique, inverse = np.unique(np.round(vertices,6),axis=0,return_inverse=True)
parents = np.arange(len(unique))
def root(i):
    while parents[i] != i:
        parents[i] = parents[parents[i]]; i = parents[i]
    return i
for a0, a1, a2 in inverse[triangles]:
    parents[root(a1)] = root(a0); parents[root(a2)] = root(a0)
labels = np.array([root(i) for i in range(len(unique))])
hook_id = labels[np.argmax(unique[:,0])]
hook_faces = triangles[labels[inverse[triangles[:,0]]] == hook_id]
assert len(hook_faces) == 250, len(hook_faces)
used, mapped = np.unique(hook_faces, return_inverse=True)
verts = vertices[used].tolist(); faces = mapped.reshape(-1, 3).tolist()
profile = [(-1.119924,.010),(-1.104,.017),(-1.065,.017),(-1.055,.0126),
           (-.86,.0126),(-.851,.0175),(-.785,.0175),(-.778,.0145),
           (-.712,.0155),(-.707,.0175),(-.645,.0175),(-.637,.011),
           (-.105,.011),(-.096,.018),(-.065,.018),(-.055,.016),(.115,.016),
           (.118,.016),(.129,.015),(.151,.016),(.164,.015),(.185,.016),(.201,.011),
           (.23,.012),(.233,.017),(.238,.018),(.243,.016),(.341,.016),(.346,.018),
           (.35,.012),(.36,.009)]
rings = []
for z, radius in profile:
    ring = []
    for i in range(10):
        ring.append(len(verts)); angle = i * math.tau / 10
        verts.append((radius*math.cos(angle), radius*math.sin(angle), z))
    rings.append(ring)
for left, right in zip(rings, rings[1:]):
    for i in range(10):
        j = (i+1)%10; faces.append([left[i],left[j],right[j],right[i]])
faces.extend([rings[0][::-1],rings[-1]])
me = bpy.data.meshes.new('Staff866'); me.from_pydata(verts, [], faces); me.update()
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=.000001)
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); bm.to_mesh(me); bm.free()
for face in me.polygons: face.use_smooth = True
low = bpy.data.objects.new('Staff', me); bpy.context.collection.objects.link(low)
mat = bpy.data.materials.new('HookedStaff_A'); mat.use_nodes = True; me.materials.append(mat)
for obj in bpy.context.scene.objects: obj.select_set(obj == low)
bpy.context.view_layer.objects.active = low
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(70), island_margin=.04)
bpy.ops.object.mode_set(mode='OBJECT')
me.calc_loop_triangles(); assert len(me.loop_triangles) == 866, len(me.loop_triangles)
scene = bpy.context.scene; scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 1
scene.render.threads_mode = 'FIXED'; scene.render.threads = 4
bake = scene.render.bake; bake.use_selected_to_active = True; bake.use_cage = False
bake.cage_extrusion = .022; bake.max_ray_distance = .05; bake.margin = 16; bake.use_clear = True
bake.normal_space = 'TANGENT'; bake.normal_r='POS_X'; bake.normal_g='POS_Y'; bake.normal_b='POS_Z'
node = mat.node_tree.nodes.new('ShaderNodeTexImage'); mat.node_tree.nodes.active = node
baked = {}
emit = nt.nodes.new('ShaderNodeEmission')
for key in ['basecolor','metal_rough','normal']:
    if key == 'normal': nt.links.new(bs.outputs[0],output.inputs['Surface'])
    else:
        nt.links.new(images[key].outputs['Color'], emit.inputs['Color']); nt.links.new(emit.outputs[0], output.inputs['Surface'])
    image = bpy.data.images.new('staff_'+key, width=1024, height=1024, alpha=False)
    image.colorspace_settings.name = 'sRGB' if key=='basecolor' else 'Non-Color'
    node.image = image; baked[key] = image
    for obj in bpy.context.scene.objects: obj.select_set(obj in [high,low])
    bpy.context.view_layer.objects.active = low
    bpy.ops.object.bake(type='NORMAL' if key=='normal' else 'EMIT')
    image.filepath_raw = str(T/f'{key}.png'); image.file_format='PNG'; image.save(); image.pack()
    print('BAKED',key,flush=True)
nt.links.new(bs.outputs[0],output.inputs['Surface'])
nt = mat.node_tree; bs = nt.nodes.get('Principled BSDF')
def tex(key):
    n=nt.nodes.new('ShaderNodeTexImage'); n.image=baked[key]; return n
nt.links.new(tex('basecolor').outputs['Color'],bs.inputs['Base Color'])
normal=nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex('normal').outputs['Color'],normal.inputs['Color']); nt.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
sep=nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tex('metal_rough').outputs['Color'],sep.inputs[0]); nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']); nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
high.hide_render=True; high.hide_set(True)
counts=[]
for level,target in enumerate([866,474,214,86]):
    obj=low if level==0 else low.copy()
    if level:
        obj.data=low.data.copy(); scene.collection.objects.link(obj); obj.name=f'Staff_LOD{level}'
        for other in scene.objects: other.select_set(other==obj)
        bpy.context.view_layer.objects.active=obj
        mod=obj.modifiers.new('Fixed reduction target','DECIMATE'); mod.ratio=target/866; mod.use_collapse_triangulate=True
        bpy.ops.object.modifier_apply(modifier=mod.name)
    # Fit only coarse grip surfaces to the accepted simplified fingers; the hook and attachment frame stay fixed.
    if level >= 2:
        for vertex in obj.data.vertices:
            z = vertex.co.z
            factor = (.72 if level == 2 else .65) if .20 < z < .355 else (.90 if level == 3 and -.10 < z < .12 else 1.)
            vertex.co.x *= factor; vertex.co.y *= factor
        obj.data.update()
    obj.data.calc_loop_triangles(); counts.append(len(obj.data.loop_triangles))
    for other in scene.objects: other.select_set(other==obj)
    bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.gltf(filepath=str(W/f'staff_lod{level}.glb'),use_selection=True,export_format='GLB',
        export_yup=False,export_animations=False,export_skins=False,export_morph=False,export_attributes=False)
    obj.hide_render=level>0
for image in bpy.data.images:
    if image.has_data: image.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'source/mm6_jak1_staff.blend'))
(R/'reduction.json').write_text(json.dumps({'before':[2018,1108,503,472],'after':counts,
    'fixed_targets':[866,474,214,86],'reduction_passes':1,'hook_lod0_triangles':250,
    'shaft_sides':10,'shared_maps':str(T.relative_to(P)),'map_size':[1024,1024],
    'normal_bake':'Accepted staff geometry and accepted tangent normals, selected-to-active, OpenGL tangent space',
    'attachment_frame':'Accepted raw glTF local frame; no transform, grip origin [0,0,0]'},indent=2))
print('REDUCED STAFF',counts,flush=True)
