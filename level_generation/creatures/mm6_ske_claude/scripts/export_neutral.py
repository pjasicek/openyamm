"""Export the rest-pose skeleton without rig for Meshy retexturing: 'body' = every face of material 0 (Bone; the sword
is excluded, it takes swatches), 'head' = the Head material faces (cranium, mandible, teeth) with their own 0..1 UVs.
Args: -- <blend> <body|head> <out.glb>"""
import bpy, bmesh, sys, os
blend, which, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Skeleton_Rig']
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
src = bpy.data.objects['Skeleton']
obj = src.copy(); obj.data = src.data.copy(); obj.name = 'SkeletonNeutral'
bpy.context.scene.collection.objects.link(obj)
obj.parent = None; obj.matrix_world = src.matrix_world.copy()
for m in list(obj.modifiers):
    obj.modifiers.remove(m)
obj.vertex_groups.clear()
names = [m.name for m in obj.data.materials]
keep = names.index('Head') if which == 'head' else names.index('Bone')
bm = bmesh.new(); bm.from_mesh(obj.data)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index != keep], context='FACES')
bm.to_mesh(obj.data); bm.free()
for a in [a.name for a in obj.data.attributes if a.name in ('piece', 'sword_class')]:
    obj.data.attributes.remove(obj.data.attributes[a])
mat = bpy.data.materials.new('Neutral'); mat.use_nodes = True
obj.data.materials.clear(); obj.data.materials.append(mat)
for o in bpy.data.objects:
    o.select_set(o == obj)
bpy.context.view_layer.objects.active = obj
bpy.ops.export_scene.gltf(filepath=os.path.abspath(out), use_selection=True, export_format='GLB',
                          export_animations=False, export_skins=False, export_morph=False, export_yup=True,
                          export_attributes=False)
print('NEUTRAL', which, out, len(obj.data.polygons), 'faces')
